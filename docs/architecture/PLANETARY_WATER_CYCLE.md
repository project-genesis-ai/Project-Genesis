# Planetary Water Cycle

The planetary water cycle is an authoritative deterministic coupling from terrain and regional weather into surface hydrology and groundwater.

## Tick flow

1. Terrain supplies elevation, land/ocean classification, and coordinates.
2. `RegionalWeatherEngine` computes spatially coupled atmospheric states for the complete grid.
3. `HydrologyEngine` converts rainfall, temperature, humidity, wind, soil capacity, and surface storage into evaporation, infiltration, runoff, river flow, lake storage, and groundwater recharge.
4. `GroundwaterEngine` carries recharge into an immutable aquifer next state and applies natural discharge/extraction limits.
5. `HydrologyEngine.route_water` maps each cell to a deterministic downstream route and basin.
6. Basin aggregation preserves runoff accounting across the complete grid.

## Invariants

- All state quantities are non-negative.
- Humidity remains in `[0, 1]`.
- Water balance is `rainfall + surface_storage = evaporation + infiltration + runoff` within floating-point tolerance.
- The cycle is deterministic for the same terrain, tick, and input snapshots.
- Caller-owned groundwater state is never mutated.
- Ragged grids and invalid capacities are rejected before simulation.

The API intentionally returns immutable dataclasses so the core simulation can snapshot, replay, and compare complete environmental ticks without hidden mutable state.
