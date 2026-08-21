import pytest
from genesis.infrastructure import UtilityNetwork, UtilityNode
from genesis.physics import Energy

def test_water_demand_uses_litres_and_days():
    node = UtilityNode("town", population=1000, water_m3=100.0)
    consumed = node.consume_water(150.0, 1.0)
    assert consumed == pytest.approx(100.0)
    assert node.water_m3 == pytest.approx(0.0)

def test_electricity_consumption_uses_joules():
    node = UtilityNode("town", electricity=Energy.from_kilowatt_hours(1.0))
    consumed = node.consume_electricity(1000.0, 1800.0)
    assert consumed.kilowatt_hours == pytest.approx(0.5)
    assert node.electricity.kilowatt_hours == pytest.approx(0.5)

def test_network_aggregates_utilities():
    network = UtilityNetwork()
    network.add(UtilityNode("a", water_m3=10.0, electricity=Energy(100)))
    network.add(UtilityNode("b", water_m3=5.0, electricity=Energy(50)))
    assert network.total_water_m3() == pytest.approx(15.0)
    assert network.total_electricity().joules == pytest.approx(150.0)
