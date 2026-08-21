from genesis.agents.agent import Agent
from genesis.cognition.runtime import CognitionRuntime
from genesis.core.simulation import Simulation


def test_cognition_observation_is_persisted_and_bounded_by_novelty() -> None:
    agent = Agent("a1", "Asha")
    world = Simulation().state.world
    world.resources["food"] = 10.0
    runtime = CognitionRuntime()

    first = runtime.observe(agent, world, 1)
    second = runtime.observe(agent, world, 2)

    assert first.perception.nearby_resources == ("food",)
    assert second.perception.nearby_resources == ("food",)
    assert len(agent.memory.memories) == 1
    assert agent.memory.recall("resources", limit=1)[0].content == "food"


def test_action_and_outcome_are_recorded() -> None:
    agent = Agent("a1", "Asha")
    runtime = CognitionRuntime()

    runtime.record_action(agent, 3, "rest", "recover energy")
    runtime.record_outcome(agent, 3, "energy:0.25", importance=0.8)

    assert [m.subject for m in agent.memory.memories] == ["actions", "outcomes"]
    assert agent.memory.recall("outcomes", 1)[0].content == "energy:0.25"


def test_simulation_tick_executes_cognition_without_changing_policy_contract() -> None:
    simulation = Simulation()
    agent = Agent("a1", "Asha")
    agent.inventory["food"] = 1.0
    simulation.add_agent(agent)
    simulation.state.world.resources["food"] = 1.0

    simulation.step()

    subjects = {memory.subject for memory in agent.memory.memories}
    assert "actions" in subjects
    assert "outcomes" in subjects
