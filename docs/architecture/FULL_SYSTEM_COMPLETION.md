# Full-System Completion Architecture

Genesis contains authoritative implementations for planetary physics, climate, hydrology, ecology, evolution, life, cognition, society, civilization, politics, economy, education, knowledge and technology. The completion layer composes those authorities; it does not create duplicate state ownership.

## 15-phase integration contract

1. **Universal biology** — `genesis.life`, `genesis.biology` and `PlanetEcologyRuntime` remain authoritative; completion derives cross-domain signals.
2. **Living ecosystem** — food web, ecology, migration, disease and population systems feed the canonical ecosystem.
3. **Planet and climate** — terrain, atmosphere/weather, hydrology, groundwater, ocean and water-cycle runtimes advance through `Simulation`.
4. **Evolution** — genetics and evolution operate on the canonical ecosystem with deterministic lineage state.
5. **Animal behavior** — organism behavior, physiology and migration remain in the life layer.
6. **Human system** — cognition, needs, health, demography and environment-driven decisions remain in the agent/simulation layers.
7. **Society/civilization** — social, culture, settlement, agriculture, government and politics remain authoritative.
8. **Economy/governance** — `GovernanceRuntime` is bound directly to `SimulationState.governments` and `SimulationState.wallets`; taxation, service spending and private transfers conserve the canonical money supply.
9. **Knowledge/technology** — research teams produce evidence-backed technology lessons; verified institutional knowledge transfers deterministically across living agents.
10. **Autonomous engineering** — `EngineeringLoop` is resumable, evidence-bearing and supports conditional human approval for high-impact work.
11. **Scale** — `PopulationScaler` produces stable region partitions with explicit individual/hybrid/aggregate LOD without changing simulation semantics.
12. **Verification** — `verify_simulation` performs invariant checks plus an independent twin-run checkpoint comparison; `verify_determinism` remains available for factory-based replay tests.
13. **Hardening** — `audit_state` checks finite values, non-negative resources/wallets, bounded health/governance and balanced double-entry accounting without mutating state.
14. **Cross-domain emergence** — `EmergenceRuntime` derives bounded ecological, civilizational, technological, migration and resilience signals and records deterministic macro-regime transitions without becoming a second authority.
15. **Finalization/scientific validation** — `run_final_validation` executes a seeded multi-agent long-run probe, audits every tick, checks checkpoint stability, verifies independent replay equality and rejects non-finite final metrics.

## Final acceptance gates

The full build is complete only when all of these hold:

- the authoritative `Simulation` remains the only mutable simulation state owner;
- governance registries alias the canonical government/wallet mappings;
- technology research has deterministic provenance and knowledge transfer;
- engineering stages can resume from persisted successful evidence;
- high-impact engineering cannot bypass `HUMAN_GATE`;
- scale plans are deterministic and LOD-aware;
- verification proves future-state replay equality rather than merely reporting `deterministic=True`;
- hardening reports all discovered faults instead of silently repairing them;
- cross-domain emergence remains derived-only and deterministic;
- the final seeded long-run probe completes 100 steps with per-tick invariant/hardening checks;
- independent twin runs produce identical final checkpoint digests;
- final metrics remain finite;
- the complete pytest suite, compile gate, integrated phase gate, determinism gate, final scientific gate and smoke gate pass.

`GenesisRuntime` is the single external facade for advancing the authoritative simulation, deriving runtime signals, producing a scale plan, executing verification/hardening checks and invoking the final acceptance probe.
