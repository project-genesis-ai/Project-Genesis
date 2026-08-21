from genesis.life.genetics import Genome
from genesis.life.organism import Organism
from genesis.life.species import Species, TrophicLevel
from genesis.physics.vectors import Vec3
from genesis.planet.coupling import PlanetEngine
from genesis.planet.runtime import PlanetEcologyRuntime
from genesis.planet.terrain import TerrainParams


def test_planetary_ecology_applies_environmental_stress() -> None:
    planet = PlanetEngine(TerrainParams(width=12, height=12, seed=4))
    snapshot = planet.step(1)
    species = Species(
        species_id="herb",
        common_name="Herbivore",
        trophic_level=TrophicLevel.HERBIVORE,
        mature_age_ticks=3,
        max_age_ticks=30,
        reproduction_probability=0.5,
        movement_speed_mps=2,
        reference_genome=Genome(),
    )
    organism = Organism("o1", species, position=Vec3(1, 0, 1), health=1.0)
    runtime = PlanetEcologyRuntime()
    stress = runtime.habitat_stress(snapshot, organism)
    assert 0 <= stress <= 1


def test_terrain_and_river_topology_are_cached_between_steps() -> None:
    planet = PlanetEngine(TerrainParams(width=10, height=10, seed=8))
    first = planet.step(1)
    second = planet.step(2)
    assert first.topology is second.topology
    assert first.routes is second.routes
    assert len(first.rivers.segments) == 100
    assert len(second.rivers.segments) == 100
