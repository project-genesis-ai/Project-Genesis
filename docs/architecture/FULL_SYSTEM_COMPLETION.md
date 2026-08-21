# Full-System Completion Architecture

Genesis already contains authoritative implementations for planetary physics, climate, hydrology, ecology, evolution, life, cognition, society, civilization, politics, economy, education, knowledge and technology. This completion layer deliberately does not create duplicate authorities.

## 13-phase integration contract

1. Universal biology: `genesis.life`, `genesis.biology`, and `PlanetEcologyRuntime` remain authoritative; `CompletionRuntime` derives population, biomass and environmental stress signals.
2. Living ecosystem: food web, ecology, migration, disease and population systems feed the canonical ecosystem.
3. Planet and climate: terrain, atmosphere, weather, hydrology, groundwater, ocean and water-cycle runtimes advance through the canonical `Simulation`.
4. Evolution: genetics and evolution runtimes operate on the canonical ecosystem.
5. Animal behavior: organism behavior, physiology and migration remain in the life layer.
6. Human system: cognition, needs, health, demography and environment-driven decisions remain in the agent/simulation layers.
7. Society/civilization: social, culture, settlement, agriculture, government and politics remain authoritative.
8. Economy: labor, resources, markets, trade, finance and double-entry ledger remain authoritative.
9. Knowledge/technology: education, knowledge transfer, research and technology remain authoritative.
10. Autonomous engineering: `EngineeringLoop` provides deterministic research → architecture → implementation → integration → test → debug → review → CI → human gate → ship stage contracts.
11. Scale: `PopulationScaler` and `ScaleController` expose deterministic region/LOD planning without changing simulation semantics.
12. Verification: checkpoint determinism plus invariant validation is exposed through `verify_simulation` and `verify_determinism`.
13. Hardening: finite-state, non-negative resource/wallet and bounded-health checks are exposed through `audit_state`.

`GenesisRuntime` is the single facade for advancing the complete authoritative simulation once, deriving cross-domain signals, producing a scale plan and running verification/hardening gates.
