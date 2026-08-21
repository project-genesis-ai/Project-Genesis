from genesis.core.state import SimulationState
from genesis.life.systems import LifeSystem
from genesis.planet import TerrainParams
from genesis.world.environment import Biome, EnvironmentCell


def test_planet_snapshot_is_mirrored_into_life_environment() -> None:
    state = SimulationState()
    state.planet = state.planet.__class__(TerrainParams(width=6, height=5, seed=12))

    state.advance_planet(1)

    assert len(state.environment.cells) == 30
    first = state.environment.cells["0:0"]
    source = state.planet_snapshot.cells[0][0]
    assert first.x == 0 and first.y == 0
    assert first.temperature_c == source.atmosphere.temperature_c
    assert first.rainfall_mm == source.atmosphere.precipitation_mm
    assert first.vegetation == source.biome.vegetation_productivity


def test_life_does_not_advance_a_second_environment_when_planet_is_authoritative() -> None:
    state = SimulationState()
    state.planet = state.planet.__class__(TerrainParams(width=4, height=4, seed=4))
    state.advance_planet(3)
    before = {
        key: (cell.temperature_c, cell.rainfall_mm, cell.water_mm, cell.vegetation)
        for key, cell in state.environment.cells.items()
    }

    LifeSystem().step(
        state.environment,
        state.ecosystem,
        ticks=1,
        simulation_tick=3,
        planet_snapshot=state.planet_snapshot,
    )

    after = {
        key: (cell.temperature_c, cell.rainfall_mm, cell.water_mm, cell.vegetation)
        for key, cell in state.environment.cells.items()
    }
    assert after == before


def test_planet_sync_preserves_legacy_environment_cells() -> None:
    state = SimulationState()
    state.planet = state.planet.__class__(TerrainParams(width=3, height=3, seed=9))
    state.environment.add_cell(
        EnvironmentCell(
            "legacy-forest",
            Biome.FOREST,
            temperature_c=24.0,
            vegetation=0.4,
        )
    )

    state.advance_planet(1)

    assert state.environment.cell("legacy-forest").vegetation == 0.4
    assert "0:0" in state.environment.cells
