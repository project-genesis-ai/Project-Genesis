from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Index, Integer, LargeBinary, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def uid() -> str:
    return str(uuid4())


def created_at() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SimulationRun(Base):
    __tablename__ = "simulation_runs"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=uid)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    engine_version: Mapped[str] = mapped_column(String(128), nullable=False)
    seed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    current_tick: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class WorldSnapshot(Base):
    __tablename__ = "world_snapshots"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=uid)
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    tick: Mapped[int] = mapped_column(BigInteger, nullable=False)
    state: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    digest: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = created_at()
    __table_args__ = (UniqueConstraint("run_id", "tick", name="uq_world_snapshot_tick"), Index("ix_world_snapshot_run_tick", "run_id", "tick"))


class AgentRecord(Base):
    __tablename__ = "agents"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    species: Mapped[str | None] = mapped_column(String(128))
    sex: Mapped[str | None] = mapped_column(String(32))
    birth_tick: Mapped[int | None] = mapped_column(BigInteger)
    death_tick: Mapped[int | None] = mapped_column(BigInteger)
    x: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    y: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    health: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    life_state: Mapped[str | None] = mapped_column(String(64))
    traits: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    needs: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    goals: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    skills: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    occupation: Mapped[str | None] = mapped_column(String(256))
    education: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    wealth: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    assets: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    current_state: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    __table_args__ = (Index("ix_agents_run_location", "run_id", "x", "y"), Index("ix_agents_run_alive", "run_id", "death_tick"))


class MemoryRecord(Base):
    __tablename__ = "memories"
    id: Mapped[str] = mapped_column(String(256), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    subject: Mapped[str] = mapped_column(String(256), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    memory_type: Mapped[str | None] = mapped_column(String(64))
    event_id: Mapped[str | None] = mapped_column(String(256))
    created_tick: Mapped[int] = mapped_column(BigInteger, nullable=False)
    location: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    importance: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (Index("ix_memories_agent_tick", "agent_id", "created_tick"), Index("ix_memories_agent_importance", "agent_id", "importance"))


class ExperienceRecord(Base):
    __tablename__ = "experiences"
    id: Mapped[str] = mapped_column(String(256), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    actor_id: Mapped[str] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    domain: Mapped[str] = mapped_column(String(128), nullable=False)
    tick: Mapped[int] = mapped_column(BigInteger, nullable=False)
    observation: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[str] = mapped_column(Text, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    consequence: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    __table_args__ = (Index("ix_experiences_actor_tick", "actor_id", "tick"), Index("ix_experiences_domain_tick", "domain", "tick"))


class RelationshipRecord(Base):
    __tablename__ = "relationships"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=uid)
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    source_agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    target_agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(64), nullable=False)
    trust: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    affinity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    started_tick: Mapped[int | None] = mapped_column(BigInteger)
    ended_tick: Mapped[int | None] = mapped_column(BigInteger)
    history: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    __table_args__ = (UniqueConstraint("run_id", "source_agent_id", "target_agent_id", "relationship_type", name="uq_relationship"), Index("ix_relationship_source", "source_agent_id"), Index("ix_relationship_target", "target_agent_id"))


class FamilyEvent(Base):
    __tablename__ = "family_events"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=uid)
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    tick: Mapped[int] = mapped_column(BigInteger, nullable=False)
    participants: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    __table_args__ = (Index("ix_family_events_run_tick", "run_id", "tick"),)


class KnowledgeRecord(Base):
    __tablename__ = "knowledge"
    id: Mapped[str] = mapped_column(String(256), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    domain: Mapped[str] = mapped_column(String(128), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    generation: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    evidence_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    discovered_by: Mapped[str | None] = mapped_column(ForeignKey("agents.id", ondelete="SET NULL"))
    discovered_tick: Mapped[int | None] = mapped_column(BigInteger)
    __table_args__ = (Index("ix_knowledge_domain", "run_id", "domain"),)


class EconomicAccount(Base):
    __tablename__ = "economic_accounts"
    id: Mapped[str] = mapped_column(String(256), primary_key=True, default=uid)
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    owner_agent_id: Mapped[str | None] = mapped_column(ForeignKey("agents.id", ondelete="SET NULL"))
    owner_business_id: Mapped[str | None] = mapped_column(String(256))
    currency: Mapped[str] = mapped_column(String(32), nullable=False)
    balance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    account_type: Mapped[str] = mapped_column(String(64), nullable=False)


class JobRecord(Base):
    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(String(256), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    occupation: Mapped[str] = mapped_column(String(256), nullable=False)
    employer_id: Mapped[str | None] = mapped_column(String(256))
    started_tick: Mapped[int] = mapped_column(BigInteger, nullable=False)
    ended_tick: Mapped[int | None] = mapped_column(BigInteger)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    __table_args__ = (Index("ix_jobs_agent", "agent_id"),)


class TransactionRecord(Base):
    __tablename__ = "transactions"
    id: Mapped[str] = mapped_column(String(256), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    tick: Mapped[int] = mapped_column(BigInteger, nullable=False)
    debit_account: Mapped[str] = mapped_column(ForeignKey("economic_accounts.id"), nullable=False)
    credit_account: Mapped[str] = mapped_column(ForeignKey("economic_accounts.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    transaction_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    __table_args__ = (Index("ix_transactions_run_tick", "run_id", "tick"),)


class SettlementRecord(Base):
    __tablename__ = "settlements"
    id: Mapped[str] = mapped_column(String(256), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("settlements.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    settlement_type: Mapped[str] = mapped_column(String(64), nullable=False)
    founded_tick: Mapped[int | None] = mapped_column(BigInteger)
    abandoned_tick: Mapped[int | None] = mapped_column(BigInteger)
    location: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    population: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    state: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    __table_args__ = (Index("ix_settlements_run_parent", "run_id", "parent_id"),)


class HistoricalEvent(Base):
    __tablename__ = "historical_events"
    id: Mapped[str] = mapped_column(String(256), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    tick: Mapped[int] = mapped_column(BigInteger, nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    participants: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    location: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    causes: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    consequences: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    __table_args__ = (Index("ix_historical_events_run_tick", "run_id", "tick"), Index("ix_historical_events_type_tick", "event_type", "tick"))


class DecisionRecord(Base):
    __tablename__ = "decisions"
    id: Mapped[str] = mapped_column(String(256), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    tick: Mapped[int] = mapped_column(BigInteger, nullable=False)
    available_choices: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    chosen_action: Mapped[str] = mapped_column(String(256), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[str | None] = mapped_column(Text)
    consequences: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    context: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    __table_args__ = (Index("ix_decisions_agent_tick", "agent_id", "tick"),)


class GeneticRecord(Base):
    __tablename__ = "genetics"
    id: Mapped[str] = mapped_column(String(256), primary_key=True, default=uid)
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(256), nullable=False)
    parent_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    species_id: Mapped[str | None] = mapped_column(String(256))
    generation: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    inherited_traits: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    mutations: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    tick: Mapped[int] = mapped_column(BigInteger, nullable=False)
    milestone: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (Index("ix_genetics_entity_tick", "entity_id", "tick"), Index("ix_genetics_species_generation", "species_id", "generation"))


class Checkpoint(Base):
    __tablename__ = "checkpoints"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=uid)
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    tick: Mapped[int] = mapped_column(BigInteger, nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    digest: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_state: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    canonical_state_blob: Mapped[bytes | None] = mapped_column(LargeBinary)
    state_blob: Mapped[bytes | None] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = created_at()
    __table_args__ = (UniqueConstraint("run_id", "tick", name="uq_checkpoint_run_tick"), Index("ix_checkpoint_run_tick", "run_id", "tick"))
