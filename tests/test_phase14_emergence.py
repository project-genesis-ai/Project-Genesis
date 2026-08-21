from genesis.agents.agent import Agent
from genesis.core.state import SimulationState
from genesis.world.emergence import EmergenceRuntime


def test_emergence_signal_is_bounded_and_deterministic() -> None:
    state_a = SimulationState()
    state_a.add_agent(Agent("a", "A", health=0.9, wealth=50.0))
    state_b = SimulationState()
    state_b.add_agent(Agent("a", "A", health=0.9, wealth=50.0))

    first = EmergenceRuntime().signal(state_a, 10)
    second = EmergenceRuntime().signal(state_b, 10)

    assert first == second
    for value in (
        first.ecological_health,
        first.civilization_strain,
        first.technology_opportunity,
        first.migration_pressure,
        first.resilience,
    ):
        assert 0.0 <= value <= 1.0


def test_emergence_regime_transition_is_auditable() -> None:
    state = SimulationState()
    runtime = EmergenceRuntime()

    transition = runtime.step(state, 1)

    assert transition is not None
    assert transition.tick == 1
    assert transition.previous_regime == "stable"
    assert transition.regime in {"stable", "innovation", "flourishing", "strain", "crisis"}
    assert runtime.transitions[-1] == transition


def test_emergence_history_is_bounded() -> None:
    state = SimulationState()
    runtime = EmergenceRuntime(max_history=2)

    for tick in range(10):
        runtime.step(state, tick)

    assert len(runtime.transitions) <= 2
