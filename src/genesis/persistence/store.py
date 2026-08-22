from __future__ import annotations

import os
import pickle
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from genesis.core.checkpoint import AuditCheckpoint, _canonical, build_checkpoint
from genesis.core.genesis_runtime import GenesisRuntime
from genesis.persistence.models import AgentRecord, Checkpoint, ExperienceRecord, HistoricalEvent, MemoryRecord, SimulationRun, WorldSnapshot

SCHEMA_VERSION = 1
ENGINE_VERSION = "0.1.0"


def database_url() -> str | None:
    value = os.getenv("DATABASE_URL", "").strip()
    if not value:
        return None
    if value.startswith("postgres://"):
        value = "postgresql+psycopg://" + value[len("postgres://") :]
    elif value.startswith("postgresql://"):
        value = "postgresql+psycopg://" + value[len("postgresql://") :]
    return value


class PersistenceError(RuntimeError):
    pass


class GenesisStore:
    """Durable store for important state; transient simulation state remains in memory."""

    def __init__(self, url: str | None = None) -> None:
        self.url = url or database_url()
        if not self.url:
            raise PersistenceError("DATABASE_URL is not configured")
        self.engine = create_engine(self.url, pool_pre_ping=True, pool_recycle=1800)
        self.sessions = sessionmaker(self.engine, expire_on_commit=False)

    @contextmanager
    def session(self) -> Iterator[Session]:
        with self.sessions.begin() as session:
            yield session

    def ensure_run(self, runtime: GenesisRuntime) -> str:
        with self.session() as session:
            run = session.scalar(select(SimulationRun).order_by(SimulationRun.created_at).limit(1))
            if run is None:
                run = SimulationRun(engine_version=ENGINE_VERSION, seed=runtime.simulation.config.seed, schema_version=SCHEMA_VERSION)
                session.add(run)
            return run.id

    def save(self, runtime: GenesisRuntime, run_id: str | None = None) -> AuditCheckpoint:
        checkpoint = build_checkpoint(runtime.simulation)
        run_id = run_id or self.ensure_run(runtime)
        state_blob = pickle.dumps(runtime.simulation, protocol=pickle.HIGHEST_PROTOCOL)
        with self.session() as session:
            run = session.get(SimulationRun, run_id)
            if run is None:
                raise PersistenceError(f"unknown simulation run: {run_id}")
            run.current_tick = checkpoint.tick
            session.add(Checkpoint(run_id=run_id, tick=checkpoint.tick, schema_version=SCHEMA_VERSION, digest=checkpoint.digest, canonical_state=checkpoint.payload, state_blob=state_blob))
            session.add(WorldSnapshot(run_id=run_id, tick=checkpoint.tick, state=checkpoint.payload.get("planet", {}), digest=checkpoint.digest))
            self._save_agents(session, runtime, run_id)
            self._save_knowledge(session, runtime, run_id)
            self._save_events(session, runtime, run_id)
        return checkpoint

    def _save_agents(self, session: Session, runtime: GenesisRuntime, run_id: str) -> None:
        state = runtime.simulation.state
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
            for memory in agent.memory.memories:
                if session.get(MemoryRecord, memory.memory_id) is None:
                    session.add(MemoryRecord(id=memory.memory_id, run_id=run_id, agent_id=agent.agent_id, subject=memory.subject, content=memory.content, created_tick=memory.created_tick, importance=memory.importance, confidence=memory.confidence))

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
            if checkpoint is None or checkpoint.state_blob is None:
                return False
            if checkpoint.schema_version != SCHEMA_VERSION:
                raise PersistenceError(f"unsupported checkpoint schema {checkpoint.schema_version}")
            simulation = pickle.loads(checkpoint.state_blob)
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
