# Planetary Water Cycle

The planetary water cycle is the authoritative deterministic coupling from terrain and regional weather into surface hydrology, groundwater, basin routing, and civilization water demand.

## Tick flow

1. Terrain supplies elevation, land/ocean classification, and coordinates.
2. `PlanetEngine` computes one spatially coupled `RegionalWeatherEngine` snapshot for the complete grid.
3. `PlanetaryWaterCycleEngine` consumes that exact weather snapshot, so atmospheric forcing is not recomputed by a second pipeline.
4. `HydrologyEngine` converts rainfall, temperature, humidity, wind, soil capacity, and surface storage into evaporation, infiltration, runoff, and groundwater recharge.
5. `GroundwaterEngine` carries persistent aquifer state forward and applies natural discharge plus validated civilization extraction demand.
6. `HydrologyRuntime.commit_cell` persists the already-computed authoritative aquifer transition without stepping groundwater a second time.
7. `HydrologyEngine.route_water` maps each cell to a deterministic downstream route and basin; river construction consumes the same authoritative runoff values.
8. Water quality, biome moisture, aquatic ecology, and civilization feedback consume the resulting persistent state.

## Invariants

- All state quantities are non-negative.
- Humidity remains in `[0, 1]`.
- Water balance is `rainfall + surface_storage = evaporation + infiltration + runoff` within floating-point tolerance.
- The cycle is deterministic for the same terrain, tick, and input snapshots.
- Caller-owned groundwater state is never mutated.
- Civilization water demand is non-negative and is applied exactly once per tick.
- The persistent groundwater value exposed by `PlanetCellState.hydrology.groundwater_mm` equals the authoritative runtime aquifer storage.
- Ragged grids and invalid capacities are rejected before simulation.

The API intentionally returns immutable dataclasses so the core simulation can snapshot, replay, and compare complete environmental ticks without hidden mutable state. The deterministic core has no database/API dependency; external persistence or service adapters can consume these snapshots without becoming a second simulation authority.
