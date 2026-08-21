from genesis.agents.agent import Agent
from genesis.core.config import SimulationConfig
from genesis.core.simulation import Simulation


def test_agent_survival_policy_consumes_food() -> None:
    simulation = Simulation()
    agent = Agent("a1", "Ada", inventory={"food": 1.0}, wealth=0.0)
    agent.needs.hunger = 0.8
    simulation.add_agent(agent)

    simulation.step()

    assert agent.inventory == {}
    assert agent.needs.hunger < 0.8
    assert simulation.state.history.events[-1].event_type == "AgentActionCompleted"
    assert simulation.state.history.events[-1].data["action"] == "eat"


def test_needs_increase_deterministically_when_no_matching_resource() -> None:
    config = SimulationConfig(
        hunger_per_tick=0.1,
        thirst_per_tick=0.2,
        energy_per_tick=0.0,
        social_per_tick=0.0,
        comfort_per_tick=0.0,
    )
    simulation = Simulation(config=config)
    agent = Agent("a1", "Ada")
    simulation.add_agent(agent)

    simulation.step()

    assert agent.needs.hunger == 0.1
    assert agent.needs.thirst == 0.2
    assert simulation.state.history.events[-1].event_type == "AgentIdle"


def test_rest_is_selected_when_energy_is_highest_need() -> None:
    simulation = Simulation()
    agent = Agent("a1", "Ada")
    agent.needs.energy = 0.9
    simulation.add_agent(agent)

    simulation.step()

    assert agent.needs.energy < 0.9
    assert simulation.state.history.events[-1].event_type == "AgentRested"
