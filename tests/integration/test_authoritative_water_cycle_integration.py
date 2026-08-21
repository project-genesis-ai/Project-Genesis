from genesis.planet import EnvironmentalImpact, PlanetEngine, TerrainParams


def test_planet_engine_uses_authoritative_water_cycle_and_persists_aquifers() -> None:
    engine = PlanetEngine(TerrainParams(width=8, height=8, seed=23))
    first = engine.step(0)

    assert engine.water_cycle.hydrology is engine.hydrology
    assert engine.water_cycle.groundwater is engine.hydrology_runtime.groundwater_engine
    assert first.cells

    land = next(cell.terrain for row in first.cells for cell in row if cell.terrain.land)
    key = (land.x, land.y)
    engine.set_civilization_impacts({
        key: EnvironmentalImpact(
            population_pressure=0.0,
            agriculture_pressure=0.0,
            land_conversion=0.0,
            water_extraction=20.0,
            pollution=0.0,
        )
    })
    second = engine.step(1)
    cell = second.cells[land.y][land.x]
    runtime = engine.hydrology_runtime.cells[key]

    assert runtime.groundwater == engine.hydrology_runtime.groundwater[key]
    assert runtime.groundwater.storage_mm == cell.hydrology.groundwater_mm
    assert runtime.pollution == 0.0
    assert 0.0 <= runtime.surface_water_quality <= 1.0


def test_authoritative_water_cycle_preserves_cell_balance_in_planet_engine() -> None:
    engine = PlanetEngine(TerrainParams(width=6, height=6, seed=9))
    snapshot = engine.step(4)

    for row in snapshot.cells:
        for cell in row:
            expected = cell.hydrology.rainfall_mm + (500.0 if not cell.terrain.land else 0.0)
            actual = (
                cell.hydrology.evaporation_mm
                + cell.hydrology.infiltration_mm
                + cell.hydrology.runoff_mm
            )
            assert abs(expected - actual) < 1e-9
