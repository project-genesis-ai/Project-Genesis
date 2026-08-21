from genesis.core.simulation import Simulation
from genesis.planet.coupling import PlanetEngine
from genesis.planet.terrain import TerrainParams


def test_simulation_advances_planet_and_water_routes() -> None:
    simulation = Simulation()
    simulation.state.planet = PlanetEngine(TerrainParams(width=16, height=12, seed=11))
    assert simulation.state.planet_snapshot is None
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
    assert first.tick != second.tick
    assert first.cells[0][0].atmosphere.temperature_c != second.cells[0][0].atmosphere.temperature_c
