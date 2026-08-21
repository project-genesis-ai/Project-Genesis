from genesis.planet.hydrology import HydrologyEngine
from genesis.planet.hydrology_runtime import HydrologyRuntime
from genesis.planet.terrain import TerrainGenerator, TerrainParams


def test_hydrology_runtime_persists_groundwater() -> None:
    grid = TerrainGenerator(TerrainParams(width=10, height=10, seed=9)).generate()
    engine = HydrologyEngine()
    state = engine.balance(
        rainfall_mm=120,
        temperature_c=20,
        humidity=0.6,
        wind_mps=2,
        soil_capacity_mm=40,
        surface_storage_mm=0,
    )
    runtime = HydrologyRuntime()
    first = runtime.step_cell((1, 1), state=state)
    second_state = engine.balance(
        rainfall_mm=40,
        temperature_c=22,
        humidity=0.7,
        wind_mps=1,
        soil_capacity_mm=40,
        surface_storage_mm=0,
    )
    second = runtime.step_cell((1, 1), state=second_state)
    assert first.groundwater.storage_mm >= 0
    assert second.groundwater.storage_mm >= 0
    assert second.groundwater.storage_mm != 0 or first.groundwater.storage_mm == 0
    routes = engine.route_water(grid)
    discharge = runtime.route_runoff(routes, {(r.x, r.y): 1.0 for r in routes})
    assert discharge
