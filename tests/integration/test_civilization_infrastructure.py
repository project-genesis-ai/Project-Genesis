from genesis.agents.agent import Agent
from genesis.core.simulation import Simulation
from genesis.civilization.government import Government
from genesis.world.disasters import Disaster, DisasterType


def test_simulation_advances_integrated_civic_and_health_state() -> None:
    simulation = Simulation()
    agent = Agent("a1", "Asha")
    simulation.add_agent(agent)
    simulation.state.add_government(Government("g1", "Genesis", population={"a1"}, treasury=100))
    simulation.state.disasters.start(Disaster("d1", DisasterType.STORM, 0.4, 1))
    simulation.state.health.states["a1"].health = 0.6
    simulation.step()
    assert agent.health >= 0.6
    assert not simulation.state.disasters.active
    assert simulation.state.culture.events[-1].kind == "disaster"
    assert simulation.state.history.all()[-1].kind == "DisasterEnded" or simulation.state.history.all()[-1].kind.startswith("Agent")
