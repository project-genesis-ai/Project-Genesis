# Project Genesis

Genesis is a deterministic, extensible world simulation written in Python. The authoritative simulation flows from planetary terrain and hydrology through ecology, life, humans, institutions, economy, knowledge and technology.

## Architecture

- **Planet authority:** deterministic terrain, topology, atmosphere/weather, rainfall, runoff, rivers, lakes/groundwater, ocean systems, biomes and planetary feedback.
- **Life authority:** ecosystems, animal populations, migration, species discovery and evolutionary lineage/speciation.
- **Human authority:** agents, physiology, needs, cognition, memory, personality, spatial position and progressive exploration/knowledge.
- **Civilization:** farms, food security, settlements, buildings, education, labor, government, politics, utilities and transport.
- **Economy:** wallets, labor compensation, trading and an append-only double-entry ledger for auditable transfers.
- **Science:** deterministic research projects unlock technologies, create innovations and propagate adoption.
- **Knowledge/culture:** social interaction, cultural transmission, generational knowledge and verified knowledge publication.
- **Auditability:** immutable simulation events, canonical checkpoints, deterministic digests, metrics and invariant validation.
- **Final validation:** a bounded long-run acceptance harness checks invariants, hardening, checkpoint stability, finite metrics and independent seeded replay.

## Running

Install development dependencies and run the complete test suite:

```bash
python -m pip install -e '.[dev]'
python -m pytest
```

The core engine has no required external service, database, network or LLM dependency. External integrations can consume the deterministic Python API without changing simulation authority.

## Determinism

Use `SimulationConfig(seed=...)` to select the authoritative planetary seed. Identical configuration and initial state produce identical planetary snapshots and canonical checkpoint digests.

## Verification

CI performs source compilation, a simulation smoke test, the complete unit/integration suite, deterministic replay checks, hardening checks, and a 100-step final scientific validation probe. The finalization contract is documented in `docs/architecture/PHASE_15_FINALIZATION.md`.
