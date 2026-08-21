from genesis.agents.agent import Agent
from genesis.core.simulation import Simulation
from genesis.core.state import SimulationState
from genesis.planet.coupling import PlanetEngine
from genesis.planet.terrain import TerrainParams


def test_small_world_survives_a_long_deterministic_run() -> None:
    simulation = Simulation(
        state=SimulationState(
            planet=PlanetEngine(TerrainParams(width=12, height=12, seed=123)),
        )
    )
    for index in range(8):
        simulation.add_agent(Agent(f"human-{index}", f"Human {index}", skills={"exploration_range": 1.0, "research": 0.2}))

    for _ in range(30):
        simulation.step()
        report = simulation.validate()
        assert report.ok, report.violations

    assert simulation.time.tick == 30
    assert simulation.metrics().event_count == len(simulation.state.history.all())
