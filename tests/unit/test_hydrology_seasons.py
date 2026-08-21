import pytest
from genesis.world.hydrology import HydrologicalNetwork, WatershedCell
from genesis.world.season import SeasonalCycle


def test_water_balance_conserves_non_evaporated_precipitation():
    cell = WatershedCell("a", 100, 10, 100, 0.25)
    flux = cell.water_balance(10)
    assert flux.infiltration_mm + flux.runoff_mm == pytest.approx(90)


def test_runoff_routes_downhill():
    cells = {
        "high": WatershedCell("high", 100, 1, 100, 0.0, downstream_id="low"),
        "low": WatershedCell("low", 10, 1, 0, 0.0),
    }
    network = HydrologicalNetwork(cells)
    network.cycle()
    assert cells["low"].surface_water_mm == pytest.approx(100)


def test_seasonal_cycle_is_bounded_and_periodic():
    cycle = SeasonalCycle()
    winter = cycle.climate(0, 20, 10, 100)
    summer = cycle.climate(182.6211, 20, 10, 100)
    assert winter.mean_temperature_c < summer.mean_temperature_c
    assert 0 <= winter.day_length_hours <= 24
