from __future__ import annotations

import hashlib
import json
import os
import pickle
import time
import zlib
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator
from uuid import uuid4

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker

from genesis.core.checkpoint import AuditCheckpoint, _canonical, build_checkpoint
from genesis.core.genesis_runtime import GenesisRuntime
from genesis.persistence.models import (
    AgentRecord,
    Checkpoint,
    ExperienceRecord,
    HistoricalEvent,
    MemoryRecord,
    SimulationRun,
    WorldSnapshot,
)

SCHEMA_VERSION = 1
ENGINE_VERSION = "0.1.0"
_COMPRESSION_MAGIC = b"GENESIS-ZLIB-1\0"
_CHUNK_SIZE = 1024 * 1024


def database_url() -> str | None:
    """Normalize a Render PostgreSQL URL without rewriting its hostname."""
    value = os.getenv("DATABASE_URL", "").strip()
    if not value:
        return None
    if value.startswith("postgres://"):
        value = "postgresql+psycopg://" + value[len("postgres://") :]
    elif value.startswith("postgresql://"):
        value = "postgresql+psycopg://" + value[len("postgresql://") :]
    if "sslmode=" not in value:
        value += ("&" if "?" in value else "?") + "sslmode=require"
    return value


class PersistenceError(RuntimeError):
    pass


def _compress(payload: bytes) -> bytes:
    return _COMPRESSION_MAGIC + zlib.compress(payload, level=6)


def _decompress(payload: bytes) -> bytes:
    if payload.startswith(_COMPRESSION_MAGIC):
        return zlib.decompress(payload[len(_COMPRESSION_MAGIC) :])
    return payload


def _chunks(payload: bytes) -> Iterator[tuple[int, bytes]]:
    for index, start in enumerate(range(0, len(payload), _CHUNK_SIZE)):
        yield index, payload[start : start + _CHUNK_SIZE]


class GenesisStore:
    """Durable store. Hot simulation state stays in RAM; durable payloads are chunked."""

    def __init__(self, url: str | None = None) -> None:
        self.url = url or database_url()
        if not self.url:
            raise PersistenceError("DATABASE_URL is not configured")
        self.engine = create_engine(
            self.url,
            pool_pre_ping=True,
            pool_recycle=900,
            pool_size=3,
            max_overflow=2,
            pool_timeout=30,
            connect_args={"connect_timeout": 10, "sslmode": "require", "keepalives": 1, "keepalives_idle": 30, "keepalives_interval": 10, "keepalives_count": 5},
        )
        self.sessions = sessionmaker(self.engine, expire_on_commit=False)

    @contextmanager
    def session(self) -> Iterator[Session]:
        with self.sessions.begin() as session:
            yield session

    def ensure_run(self, runtime: GenesisRuntime) -> str:
        for attempt in range(3):
            try:
                with self.session() as session:
                    run = session.scalar(select(SimulationRun).order_by(SimulationRun.created_at.desc()).limit(1))
                    if run is None:
                        run = SimulationRun(engine_version=ENGINE_VERSION, seed=runtime.simulation.config.seed, schema_version=SCHEMA_VERSION)
                        session.add(run)
                    session.flush()
                    return run.id
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(0.5 * (2**attempt))
        raise AssertionError("unreachable")

    def save(self, runtime: GenesisRuntime, run_id: str | None = None) -> AuditCheckpoint:
        checkpoint = build_checkpoint(runtime.simulation)
        run_id = run_id or self.ensure_run(runtime)
        canonical_bytes = json.dumps(checkpoint.payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        state_blob = _compress(pickle.dumps(runtime.simulation, protocol=pickle.HIGHEST_PROTOCOL))
        planet_bytes = _compress(json.dumps(checkpoint.payload.get("planet", {}), sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8"))
        canonical_summary = {"tick": checkpoint.tick, "digest": checkpoint.digest, "schema_version": SCHEMA_VERSION, "compressed": True, "checkpoint_bytes": len(state_blob), "planet_bytes": len(planet_bytes)}

        for attempt in range(3):
            try:
                with self.session() as session:
                    run = session.get(SimulationRun, run_id)
                    if run is None:
                        raise PersistenceError(f"unknown simulation run: {run_id}")
                    run.current_tick = checkpoint.tick
                    checkpoint_row = Checkpoint(run_id=run_id, tick=checkpoint.tick, schema_version=SCHEMA_VERSION, digest=checkpoint.digest, canonical_state=canonical_summary, canonical_state_blob=None, state_blob=None)
                    session.add(checkpoint_row)
                    session.flush()
                    for index, chunk in _chunks(state_blob):
                        session.execute(text("INSERT INTO checkpoint_chunks (id, checkpoint_id, chunk_index, data, checksum, size_bytes) VALUES (:id, :checkpoint_id, :chunk_index, :data, :checksum, :size_bytes)"), {"id": str(uuid4()), "checkpoint_id": checkpoint_row.id, "chunk_index": index, "data": chunk, "checksum": hashlib.sha256(chunk).hexdigest(), "size_bytes": len(chunk)})

                    snapshot = WorldSnapshot(run_id=run_id, tick=checkpoint.tick, state={"chunked": True, "encoding": "zlib-json", "bytes": len(planet_bytes), "schema_version": SCHEMA_VERSION}, digest=checkpoint.digest)
                    session.add(snapshot)
                    session.flush()
                    for index, chunk in _chunks(planet_bytes):
                        session.execute(text("INSERT INTO world_snapshot_chunks (id, snapshot_id, chunk_index, data, checksum, size_bytes) VALUES (:id, :snapshot_id, :chunk_index, :data, :checksum, :size_bytes)"), {"id": str(uuid4()), "snapshot_id": snapshot.id, "chunk_index": index, "data": chunk, "checksum": hashlib.sha256(chunk).hexdigest(), "size_bytes": len(chunk)})
                    self._save_agents(session, runtime, run_id)
                    self._save_knowledge(session, runtime, run_id)
                    self._save_events(session, runtime, run_id)
                return checkpoint
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(0.75 * (2**attempt))
        raise AssertionError("unreachable")

    def _save_agents(self, session: Session, runtime: GenesisRuntime, run_id: str) -> None:
        state = runtime.simulation.state
        now = datetime.now(timezone.utc)
        for agent in state.agents.values():
            row = session.get(AgentRecord, agent.agent_id)
            if row is None:
                row = AgentRecord(id=agent.agent_id, run_id=run_id, name=agent.name)
                session.add(row)
            row.name = agent.name
            row.x, row.y = agent.world_x, agent.world_y
            row.health = agent.health
            row.traits = _canonical({"personality": agent.personality, "age_ticks": agent.age_ticks})
            row.needs = _canonical(agent.needs)
            row.skills = _canonical(agent.skills)
            row.wealth = agent.wealth
            row.assets = _canonical(agent.inventory)
            row.current_state = {"knowledge": sorted(agent.knowledge)}
            person = state.demography.people.get(agent.agent_id)
            if person is not None:
                row.life_state = person.stage.value
                if not person.alive:
                    row.death_tick = runtime.simulation.time.tick
            current_memory_ids = set()
            for memory in agent.memory.memories:
                current_memory_ids.add(memory.memory_id)
                stored = session.get(MemoryRecord, memory.memory_id)
                if stored is None:
                    session.add(MemoryRecord(id=memory.memory_id, run_id=run_id, agent_id=agent.agent_id, subject=memory.subject, content=memory.content, created_tick=memory.created_tick, importance=memory.importance, confidence=memory.confidence))
                else:
                    stored.archived_at = None
            for stored in session.scalars(select(MemoryRecord).where(MemoryRecord.agent_id == agent.agent_id)).all():
                if stored.id not in current_memory_ids and stored.archived_at is None:
                    stored.archived_at = now

    def _save_knowledge(self, session: Session, runtime: GenesisRuntime, run_id: str) -> None:
        for domain in runtime.simulation.state.knowledge.domains.values():
            for experience in domain.experiences.values():
                if session.get(ExperienceRecord, experience.experience_id) is None:
                    session.add(ExperienceRecord(id=experience.experience_id, run_id=run_id, actor_id=experience.actor_id, domain=experience.domain, tick=experience.tick, observation=experience.observation, action=experience.action, outcome=experience.outcome, success=experience.success, confidence=experience.confidence))

    def _save_events(self, session: Session, runtime: GenesisRuntime, run_id: str) -> None:
        for index, event in enumerate(runtime.simulation.state.history.all()):
            event_id = f"{run_id}:{event.tick}:{index}:{event.event_type}"
            if session.get(HistoricalEvent, event_id) is None:
                data = _canonical(dict(event.data or {}))
                participants = [item for item in (event.actor_id, event.target_id) if item]
                session.add(HistoricalEvent(id=event_id, run_id=run_id, tick=event.tick, event_type=event.event_type, description=event.event_type, participants=participants, data=data))

    def load_latest(self, runtime: GenesisRuntime, run_id: str | None = None) -> bool:
        with self.session() as session:
            query = select(Checkpoint).order_by(Checkpoint.tick.desc())
            if run_id:
                query = query.where(Checkpoint.run_id == run_id)
            checkpoint = session.scalar(query.limit(1))
            if checkpoint is None:
                return False
            if checkpoint.schema_version != SCHEMA_VERSION:
                raise PersistenceError(f"unsupported checkpoint schema {checkpoint.schema_version}")
            if checkpoint.state_blob is not None:
                payload = _decompress(checkpoint.state_blob)
            else:
                rows = session.execute(text("SELECT data, checksum FROM checkpoint_chunks WHERE checkpoint_id = :checkpoint_id ORDER BY chunk_index"), {"checkpoint_id": checkpoint.id}).all()
                if not rows:
                    return False
                chunks = []
                for data, checksum in rows:
                    if hashlib.sha256(data).hexdigest() != checksum:
                        raise PersistenceError("checkpoint chunk checksum mismatch")
                    chunks.append(bytes(data))
                payload = _decompress(b"".join(chunks))
            simulation = pickle.loads(payload)
            if build_checkpoint(simulation).digest != checkpoint.digest:
                raise PersistenceError("checkpoint integrity digest mismatch")
            runtime.simulation = simulation
            return True

    def latest_checkpoint(self, run_id: str | None = None) -> Checkpoint | None:
        with self.session() as session:
            query = select(Checkpoint).order_by(Checkpoint.tick.desc())
            if run_id:
                query = query.where(Checkpoint.run_id == run_id)
            return session.scalar(query.limit(1))

    def ping(self) -> bool:
        with self.engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        return True
