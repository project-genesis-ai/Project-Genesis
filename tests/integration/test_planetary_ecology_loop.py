from genesis.core.state import SimulationState
from genesis.planet.coupling import PlanetEngine
from genesis.planet.terrain import TerrainParams


def test_planet_tick_updates_authoritative_ecology_runtime() -> None:
    state = SimulationState(planet=PlanetEngine(TerrainParams(width=8, height=8, seed=41)))

    state.advance_planet(1)

    assert state.planet_snapshot is not None
    assert state.planet_snapshot.tick == 1
    assert state.planet_ecology.terrestrial_biomass


def test_planet_ecology_state_persists_across_ticks() -> None:
    state = SimulationState(planet=PlanetEngine(TerrainParams(width=8, height=8, seed=41)))

    state.advance_planet(1)
    first = {
        name: biomass.plants
        for name, biomass in state.planet_ecology.terrestrial_biomass.items()
    }

    state.advance_planet(2)
    second = {
        name: biomass.plants
        for name, biomass in state.planet_ecology.terrestrial_biomass.items()
    }

    assert first.keys() == second.keys()
    assert any(second[name] != first[name] for name in first)
