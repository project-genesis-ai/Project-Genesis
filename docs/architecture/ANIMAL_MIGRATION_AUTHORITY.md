# Animal Migration Authority

## Root cause
The repository already had a validated `MigrationProfile`/`decide_migration` model and `AnimalMigrationRuntime`, but those decisions were only exposed as standalone APIs. No authoritative simulation tick applied them to living organisms.

## Tick flow
1. `PlanetEngine` produces the authoritative planetary snapshot.
2. `SimulationState` mirrors the snapshot into coordinate-aware environment cells.
3. `LifeSystem` derives local habitat conditions from that mirror.
4. Species with an explicit `MigrationProfile` evaluate only reachable local cells within their maximum daily distance.
5. A deterministic improvement in habitat suitability produces a `MigrationRecord` and updates the organism's x/z position using immutable `Vec3` replacement.
6. `Simulation` publishes the movement as an `AnimalMigrated` event.

Species without a migration profile remain unchanged, preserving existing behavior and keeping migration opt-in rather than inventing species-specific ecological assumptions.

## Performance
Candidate search is bounded to the local grid radius rather than scanning the complete planet for every organism. The synchronized environment also provides a coordinate index for O(1) local cell lookup.
