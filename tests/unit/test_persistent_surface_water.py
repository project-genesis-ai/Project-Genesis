from genesis.planet.terrain import TerrainCell
from genesis.planet.water_cycle import PlanetaryWaterCycleEngine


def lake_grid() -> tuple[tuple[TerrainCell, ...], ...]:
    return tuple(
        tuple(
            TerrainCell(x, y, 2.0 if (x, y) != (1, 1) else 1.0, True, 0.0)
            for x in range(4)
        )
        for y in range(4)
    )


def test_closed_depression_retains_surface_water_between_ticks() -> None:
    engine = PlanetaryWaterCycleEngine()
    grid = lake_grid()
    first = engine.run(
        grid,
        tick=0,
        moisture_by_cell={(x, y): 1.0 for y in range(4) for x in range(4)},
        surface_storage_by_cell={(x, y): 0.0 for y in range(4) for x in range(4)},
        soil_capacity_mm=0.0,
    )

    center = next(cell for cell in first.cells if (cell.x, cell.y) == (1, 1))
    assert center.hydrology.lake_storage > 0.0
    assert first.total_surface_storage_mm == 0.0
    assert first.max_balance_error_mm == 0.0

    second = engine.run(
        grid,
        tick=1,
        moisture_by_cell={(x, y): 1.0 for y in range(4) for x in range(4)},
        surface_storage_by_cell={(x, y): 0.0 for y in range(4) for x in range(4)},
        soil_capacity_mm=0.0,
    )

    center_second = next(cell for cell in second.cells if (cell.x, cell.y) == (1, 1))
    assert center_second.surface_storage_mm == center.hydrology.lake_storage
    assert second.total_surface_storage_mm >= center.hydrology.lake_storage
