from genesis.core.simulation import Simulation
from genesis.planet.terrain import TerrainParams
from genesis.planet.coupling import PlanetEngine


def test_simulation_advances_planet_and_water_routes() -> None:
    simulation = Simulation()
    simulation.state.planet = PlanetEngine(TerrainParams(width=16, height=12, seed=11))
    before = simulation.state.planet_snapshot
    assert before is None
    simulation.step()
    first = simulation.state.planet_snapshot
    assert first is not None
    assert first.tick == 1
    assert len(first.cells) == 12
    assert len(first.routes) == 16 * 12
    simulation.step()
    second = simulation.state.planet_snapshot
    assert second is not None
    assert second.tick == 2
    assert second.cells != ()
    assert first.cells != second.cells
