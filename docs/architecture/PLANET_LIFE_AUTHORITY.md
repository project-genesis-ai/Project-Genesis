# Planet/Life Environment Authority

## Root cause
The repository contains two environmental representations: the newer `PlanetEngine` and the older `genesis.world.Environment`. `Simulation.step()` advanced `LifeSystem` against the older climate model before advancing the planetary engine, creating a second climate authority. `LifeSystem._habitat_for()` also selected the first environment cell regardless of organism position.

## Architecture
- `PlanetEngine` is the authoritative environmental tick.
- `Environment` remains a compatibility mirror for legacy life/forest/behavior code.
- `SimulationState.advance_planet()` synchronizes the mirror from the immutable `PlanetSnapshot` after every planetary tick.
- `LifeSystem.step(..., planet_snapshot=...)` consumes the synchronized mirror without advancing its own climate model.
- Synchronized cells use stable `x:y` IDs and retain their actual terrain coordinates.
- Organism habitat selection chooses the nearest synchronized environment cell rather than an arbitrary first cell.

## Invariants
- A simulation tick has one atmospheric authority.
- Life receives the same temperature, rainfall, water and vegetation conditions produced by `PlanetEngine`.
- Legacy callers can still create and manually advance `Environment` when no planet snapshot is supplied.
- Stale mirrored cells are removed when the authoritative snapshot changes dimensions.
- Existing `EnvironmentCell` positional constructors remain compatible because coordinates are appended as optional fields.
