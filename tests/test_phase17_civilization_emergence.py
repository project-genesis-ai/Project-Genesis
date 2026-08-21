from genesis.agents.agent import Agent
from genesis.core.genesis_runtime import GenesisRuntime
from genesis.core.simulation import Simulation
from genesis.settlement.settlements import Settlement
from genesis.civilization.emergence import CivilizationEmergenceRuntime, CivilizationStage


def _state_with_settlement(count: int = 5):
    simulation = Simulation()
    settlement = Settlement("s1", "Origin")
    simulation.state.add_settlement(settlement)
    settlement.store("food", count * 4.0)
    for index in range(count):
        agent = Agent(f"a{index}", f"Agent {index}", wealth=100.0, knowledge={"farming", "trade"})
        simulation.add_agent(agent)
        simulation.state.assign_agent_to_settlement(agent.agent_id, settlement.settlement_id)
    return simulation


def test_civilization_stage_is_deterministic_and_bounded() -> None:
    first = _state_with_settlement()
    second = _state_with_settlement()
    runtime_a = CivilizationEmergenceRuntime()
    runtime_b = CivilizationEmergenceRuntime()

    assert runtime_a.signal(first.state, "s1", 1) == runtime_b.signal(second.state, "s1", 1)
    transitions = runtime_a.step(first.state, 1)
    assert len(transitions) == 1
    assert transitions[0].stage is CivilizationStage.CAMP
    assert 0.0 <= transitions[0].signal.food_security <= 1.0
    assert 0.0 <= transitions[0].signal.social_cohesion <= 1.0

    next_transitions = runtime_a.step(first.state, 2)
    assert len(next_transitions) == 1
    assert next_transitions[0].stage is CivilizationStage.SETTLEMENT


def test_genesis_runtime_exposes_civilization_transitions() -> None:
    runtime = GenesisRuntime()
    runtime.simulation.state.add_settlement(Settlement("s1", "Origin"))
    runtime.simulation.state.assign_agent_to_settlement
    assert runtime.civilization_transitions() == ()
