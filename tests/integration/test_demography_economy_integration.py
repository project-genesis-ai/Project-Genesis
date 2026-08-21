from genesis.agents.agent import Agent
from genesis.core.simulation import Simulation
from genesis.economy import Job


def test_simulation_pays_employed_agents_and_tracks_demography() -> None:
    simulation = Simulation()
    agent = Agent("a1", "Asha", wealth=2)
    simulation.add_agent(agent)
    simulation.state.labor.post(Job("j1", "Farmer", "farm", 3.0))
    assert simulation.state.labor.hire("a1", "j1")
    before = agent.wealth
    simulation.step()
    assert agent.wealth == before + 3.0
    assert simulation.state.demography.people["a1"].age_ticks == agent.age_ticks
