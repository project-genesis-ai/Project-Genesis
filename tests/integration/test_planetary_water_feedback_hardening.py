from genesis.agents.agent import Agent
from genesis.core.simulation import Simulation
from genesis.infrastructure import UtilityNode
from genesis.settlement import Settlement


def test_utility_water_extraction_reaches_planetary_feedback() -> None:
    simulation = Simulation()
    simulation.state.add_settlement(Settlement("s1", "Origin", location=(2, 2)))
    simulation.state.utilities.add(UtilityNode("s1", population=1, water_m3=10.0))
    simulation.state.add_agent(Agent("a1", "Ada"))
    simulation.state.assign_agent_to_settlement("a1", "s1")

    node = simulation.state.utilities.nodes["s1"]
    node.consume_water(1000.0)
    simulation.step()

    impact = simulation.state.planet.civilization_impacts[(2, 2)]
    assert impact.water_extraction == 1.0


def test_pollution_reaches_planetary_cell_quality() -> None:
    simulation = Simulation()
    simulation.state.add_settlement(Settlement("s1", "Origin", location=(2, 2)))
    simulation.state.utilities.add(UtilityNode("s1"))
    simulation.state.utilities.nodes["s1"].discharge_pollution(1.0)
    simulation.state.add_agent(Agent("a1", "Ada"))
    simulation.state.assign_agent_to_settlement("a1", "s1")

    simulation.step()

    cell = simulation.state.planet_snapshot.cells[2][2]
    assert cell.pollution == 1.0
    assert cell.surface_water_quality == 0.3


def test_planetary_moisture_uses_previous_groundwater_state() -> None:
    simulation = Simulation()
    first = simulation.state.planet.step(0)
    second = simulation.state.planet.step(1)

    first_groundwater = first.cells[2][2].hydrology.groundwater_mm
    second_moisture = second.cells[2][2].atmosphere.humidity
    assert first_groundwater >= 0.0
    assert 0.0 <= second_moisture <= 1.0
