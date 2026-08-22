from __future__ import annotations

import os

import pytest

sqlalchemy = pytest.importorskip("sqlalchemy")

from genesis.core.genesis_runtime import GenesisRuntime
from genesis.persistence.models import Base
from genesis.persistence.store import GenesisStore


def test_persistence_schema_contains_required_domains() -> None:
    expected = {
        "simulation_runs", "world_snapshots", "agents", "memories", "experiences",
        "relationships", "family_events", "knowledge", "economic_accounts", "jobs",
        "transactions", "settlements", "historical_events", "decisions", "genetics", "checkpoints",
    }
    assert expected.issubset(Base.metadata.tables)
    for table_name in expected:
        assert Base.metadata.tables[table_name].primary_key.columns


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="requires a configured PostgreSQL DATABASE_URL")
def test_postgres_connection_and_checkpoint_recovery() -> None:
    store = GenesisStore()
    assert store.ping() is True
    runtime = GenesisRuntime()
    runtime.simulation.state.initialize_planet()
    run_id = store.ensure_run(runtime)
    checkpoint = store.save(runtime, run_id)
    restored = GenesisRuntime()
    assert store.load_latest(restored, run_id) is True
    assert restored.simulation.time.tick == checkpoint.tick
    assert restored.simulation.state.planet_snapshot is not None
    assert store.latest_checkpoint(run_id).digest == checkpoint.digest
