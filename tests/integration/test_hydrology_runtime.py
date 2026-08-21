from genesis.planet.hydrology import HydrologyEngine
from genesis.planet.hydrology_runtime import HydrologyRuntime
from genesis.planet.terrain import TerrainGenerator, TerrainParams


def test_hydrology_runtime_persists_groundwater_and_routes_runoff() -> None:
    grid = TerrainGenerator(TerrainParams(width=10, height=10, seed=9)).generate()
    engine = HydrologyEngine()
    first_state = engine.balance(
        rainfall_mm=120,
        temperature_c=20,
        humidity=0.6,
        wind_mps=2,
        soil_capacity_mm=40,
        surface_storage_mm=0,
    )
    second_state = engine.balance(
        rainfall_mm=40,
        temperature_c=22,
        humidity=0.7,
        wind_mps=1,
        soil_capacity_mm=40,
        surface_storage_mm=0,
    )

    runtime = HydrologyRuntime()
    first = runtime.step_cell((1, 1), state=first_state)
    second = runtime.step_cell((1, 1), state=second_state)

    assert first.groundwater.storage_mm >= 0
    assert second.groundwater.storage_mm >= 0
    assert runtime.groundwater[(1, 1)] == second.groundwater
    assert runtime.cells[(1, 1)] == second

    routes = engine.route_water(grid)
    discharge = runtime.route_runoff(routes, {(route.x, route.y): 1.0 for route in routes})
    assert len(discharge) == len(routes)
    assert all(value >= 1.0 for value in discharge.values())


def test_hydrology_runtime_applies_water_extraction_and_pollution() -> None:
    engine = HydrologyEngine()
    state = engine.balance(
        rainfall_mm=100,
        temperature_c=20,
        humidity=0.5,
        wind_mps=2,
        soil_capacity_mm=50,
        surface_storage_mm=0,
    )
    runtime = HydrologyRuntime()

    from genesis.planet.civilization_feedback import EnvironmentalImpact

    impact = EnvironmentalImpact(
        population_pressure=0.1,
        agriculture_pressure=0.2,
        land_conversion=0.2,
        water_extraction=0.8,
        pollution=0.9,
    )
    cell = runtime.step_cell((2, 3), state=state, civilization=impact)

    assert cell.pollution == 0.9
    assert cell.surface_water_quality < 1.0
    assert cell.groundwater.discharge_mm >= 0.8
