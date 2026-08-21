from genesis.life.genetics import Genome
from genesis.life.organism import Organism
from genesis.life.species import Species, TrophicLevel
from genesis.planet.evolution_runtime import EvolutionRuntime, PopulationEnvironment


def test_environmental_isolation_can_trigger_runtime_speciation() -> None:
    species = Species(
        species_id="finch",
        common_name="Finch",
        trophic_level=TrophicLevel.HERBIVORE,
        mature_age_ticks=3,
        max_age_ticks=40,
        reproduction_probability=0.8,
        movement_speed_mps=3.0,
        carrying_capacity=100,
        reference_genome=Genome(speed_mps=2.0),
    )
    environment = PopulationEnvironment(100, 0.9, 0.9, 0.1, 25)
    result = EvolutionRuntime(seed=3).evaluate(species, environment)
    assert result is not None
    child, event = result
    assert child.species_id == "finch:g25"
    assert event.generation == 25


def test_population_trait_summary_is_stable() -> None:
    species = Species(
        species_id="hare",
        common_name="Hare",
        trophic_level=TrophicLevel.HERBIVORE,
        mature_age_ticks=2,
        max_age_ticks=20,
        reproduction_probability=0.8,
        movement_speed_mps=5.0,
    )
    organisms = (
        Organism("h1", species),
        Organism("h2", species),
    )
    traits = EvolutionRuntime().population_traits(organisms)
    assert traits["mean_speed"] >= 0
    assert traits["mean_fertility"] >= 0
    assert traits["mean_resistance"] >= 0
