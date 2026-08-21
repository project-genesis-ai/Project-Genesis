from genesis.agents.agent import Agent
from genesis.core.simulation import Simulation
from genesis.core.state import SimulationState
from genesis.planet.coupling import PlanetEngine
from genesis.planet.terrain import TerrainParams


def _run() -> tuple[tuple[int, float, tuple[str, ...]], ...]:
    state = SimulationState(planet=PlanetEngine(TerrainParams(width=16, height=16, seed=7)))
    simulation = Simulation(state=state)
    first = Agent("a", "A")
    second = Agent("b", "B")
    first.learn("tool-use")
    second.learn("food-preservation")
    simulation.add_agent(first)
    simulation.add_agent(second)
    for _ in range(4):
        simulation.step()
    return tuple(
        (
            agent.memory.memories[-1].created_tick if agent.memory.memories else -1,
            agent.health,
            tuple(sorted(agent.knowledge)),
        )
        for agent in sorted(simulation.state.agents.values(), key=lambda item: item.agent_id)
    )


def test_social_and_culture_replay_is_deterministic() -> None:
    assert _run() == _run()
