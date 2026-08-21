from __future__ import annotations

import math

import pytest

from genesis.planet import (
    GroundwaterState,
    PlanetaryWaterCycleEngine,
    TerrainGenerator,
    TerrainParams,
)


def test_planetary_water_cycle_is_deterministic_and_balanced() -> None:
    grid = TerrainGenerator(TerrainParams(width=8, height=6, seed=17)).generate()
    engine = PlanetaryWaterCycleEngine()
    groundwater = {(x, y): GroundwaterState() for y in range(6) for x in range(8)}

    first = engine.run(grid, tick=42, groundwater_by_cell=groundwater)
    second = engine.run(grid, tick=42, groundwater_by_cell=groundwater)

    assert first == second
    assert len(first.cells) == 48
    assert first.max_balance_error_mm < 1e-9
    assert first.total_rainfall_mm >= first.total_runoff_mm
    assert first.total_groundwater_storage_mm >= 0.0
    assert all(math.isfinite(cell.climate_temperature_c) for cell in first.cells)
    assert all(0.0 <= cell.humidity <= 1.0 for cell in first.cells)


def test_planetary_water_cycle_routes_runoff_into_deterministic_basins() -> None:
    grid = TerrainGenerator(TerrainParams(width=10, height=10, seed=3)).generate()
    result = PlanetaryWaterCycleEngine().run(grid, tick=1)

    assert result.basins
    assert sum(basin.contributing_cells for basin in result.basins) == 100
    assert sum(basin.accumulated_runoff_mm for basin in result.basins) == pytest.approx(
        result.total_runoff_mm
    )
    assert all(basin.accumulated_runoff_mm >= 0.0 for basin in result.basins)


def test_planetary_water_cycle_rejects_ragged_grid() -> None:
    grid = TerrainGenerator(TerrainParams(width=6, height=6, seed=2)).generate()
    ragged = (grid[0], grid[1][:-1])

    with pytest.raises(ValueError, match="rectangular"):
        PlanetaryWaterCycleEngine().run(ragged, tick=0)
