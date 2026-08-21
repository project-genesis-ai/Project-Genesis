import pytest

from genesis.planet.hydrology import HydrologyEngine


def test_water_balance_conserves_surface_water() -> None:
    engine = HydrologyEngine(infiltration_rate=0.4)
    state = engine.balance(
        rainfall_mm=100.0,
        temperature_c=25.0,
        humidity=0.5,
        wind_mps=2.0,
        soil_capacity_mm=50.0,
        surface_storage_mm=20.0,
    )

    assert state.rainfall_mm + 20.0 == pytest.approx(state.evaporation_mm + state.infiltration_mm + state.runoff_mm)
    assert state.lake_storage == pytest.approx(state.runoff_mm)
    assert state.river_flow == pytest.approx(state.runoff_mm)


def test_surface_storage_can_evaporate_without_creating_water() -> None:
    engine = HydrologyEngine()
    state = engine.balance(
        rainfall_mm=0.0,
        temperature_c=30.0,
        humidity=0.0,
        wind_mps=0.0,
        soil_capacity_mm=100.0,
        surface_storage_mm=10.0,
    )

    assert state.evaporation_mm > 0.0
    assert state.evaporation_mm + state.infiltration_mm + state.runoff_mm == pytest.approx(10.0)
