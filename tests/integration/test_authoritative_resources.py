from genesis.core.state import SimulationState
from genesis.infrastructure import UtilityNode
from genesis.physics import Energy
from genesis.resources import ResourceType

def test_simulation_state_owns_physical_resources_and_utilities():
    state = SimulationState()
    state.resources.add(ResourceType.WATER, 100.0)
    state.utilities.add(UtilityNode("settlement", population=100, water_m3=10.0, electricity=Energy.from_kilowatt_hours(2.0)))
    assert state.resources.amount(ResourceType.WATER) == 100.0
    assert state.utilities.total_water_m3() == 10.0
    assert state.utilities.total_electricity().kilowatt_hours == 2.0
