from genesis.agents.agent import Agent
from genesis.core.checkpoint import build_checkpoint
from genesis.core.config import SimulationConfig
from genesis.core.simulation import Simulation


def test_simulation_seed_controls_authoritative_planet() -> None:
    first = Simulation(config=SimulationConfig(seed=41))
    second = Simulation(config=SimulationConfig(seed=41))
    first.add_agent(Agent("a", "A"))
    second.add_agent(Agent("a", "A"))

    first.step()
    second.step()

    assert first.state.planet.terrain_params.seed == 41
    assert first.state.planet_snapshot == second.state.planet_snapshot


def test_checkpoint_digest_is_stable_for_identical_runs() -> None:
    first = Simulation(config=SimulationConfig(seed=9))
    second = Simulation(config=SimulationConfig(seed=9))
    first.add_agent(Agent("a", "A"))
    second.add_agent(Agent("a", "A"))

    first.step()
    second.step()

    assert build_checkpoint(first).digest == build_checkpoint(second).digest


def test_checkpoint_digest_changes_when_only_the_planet_seed_changes() -> None:
    first = Simulation(config=SimulationConfig(seed=11))
    second = Simulation(config=SimulationConfig(seed=12))
    first.add_agent(Agent("a", "A"))
    second.add_agent(Agent("a", "A"))

    first.step()
    second.step()

    first_checkpoint = build_checkpoint(first)
    second_checkpoint = build_checkpoint(second)

    assert first_checkpoint.digest != second_checkpoint.digest
    assert first_checkpoint.payload["planet"]["present"] is True
    assert first_checkpoint.payload["planet"]["width"] > 0
    assert first_checkpoint.payload["planet"]["height"] > 0
