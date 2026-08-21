from genesis.life.species import Species, TrophicLevel
from genesis.planet.evolution_runtime import EvolutionRuntime, PopulationEnvironment


def test_speciation_uses_observed_population_not_parent_capacity() -> None:
    species = Species(
        species_id="finch",
        common_name="Finch",
        trophic_level=TrophicLevel.HERBIVORE,
        mature_age_ticks=2,
        max_age_ticks=50,
        reproduction_probability=0.5,
        movement_speed_mps=2.0,
        carrying_capacity=1000,
    )
    result = EvolutionRuntime(seed=1).evaluate(
        species,
        PopulationEnvironment(
            population_size=1,
            isolation=1.0,
            environmental_distance=1.0,
            competition=0.0,
            generation=10,
        ),
    )
    assert result is None
