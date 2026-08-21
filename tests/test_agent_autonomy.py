from genesis.agents.agent import Agent
from genesis.core.simulation import Simulation


def test_skilled_agent_can_work_and_learn_when_survival_needs_are_satisfied() -> None:
    simulation = Simulation()
    agent = Agent(
        "autonomous",
        "Autonomous",
        wealth=10.0,
        skills={"farming": 0.5},
        knowledge={"agriculture"},
    )
    agent.needs.hunger = 0.0
    agent.needs.thirst = 0.0
    agent.needs.energy = 0.0
    agent.needs.social = 0.0
    simulation.add_agent(agent)

    before = agent.wealth
    simulation.step()

    assert agent.wealth > before or any("learned:" in item for item in agent.knowledge)
    assert any(event.actor_id == "autonomous" and event.kind in {"AgentWorked", "AgentLearned", "AgentSocialized"} for event in simulation.state.history)


def test_autonomy_is_deterministic_for_equal_initial_state() -> None:
    first = Simulation()
    second = Simulation()
    for simulation in (first, second):
        agent = Agent("a", "A", skills={"craft": 0.4}, knowledge={"craft"})
        agent.needs.hunger = agent.needs.thirst = agent.needs.energy = agent.needs.social = 0.0
        simulation.add_agent(agent)

    first.step()
    second.step()

    assert first.state.history[-1].kind == second.state.history[-1].kind
    assert first.state.agents["a"].wealth == second.state.agents["a"].wealth
    assert first.state.agents["a"].knowledge == second.state.agents["a"].knowledge
