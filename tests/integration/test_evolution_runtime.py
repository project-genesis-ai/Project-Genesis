import pytest

from genesis.life.ecosystem import Ecosystem
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
    assert child.parent_species_id == "finch"
    assert child.origin_generation == 25
    assert child.lineage_depth == 1
    assert event.generation == 25
    assert event.lineage_depth == 1


def test_speciation_applies_to_a_deterministic_live_cohort() -> None:
    species = Species(
        species_id="finch",
        common_name="Finch",
        trophic_level=TrophicLevel.HERBIVORE,
        mature_age_ticks=1,
        max_age_ticks=40,
        reproduction_probability=0.8,
        movement_speed_mps=3.0,
        carrying_capacity=20,
        reference_genome=Genome(speed_mps=2.0, fertility=1.5),
    )
    ecosystem = Ecosystem()
    ecosystem.register_species(species)
    for index in range(10):
        organism = Organism(f"f{index}", species, age_ticks=5)
        organism.genome = Genome(speed_mps=2.0 + index * 0.1, fertility=1.0)
        ecosystem.add_organism(organism)

    runtime = EvolutionRuntime(seed=7)
    application = runtime.apply_speciation(
        ecosystem,
        "finch",
        PopulationEnvironment(10, 0.9, 0.9, 0.1, 25),
    )

    assert application is not None
    assert application.event.child_species_id == "finch:g25"
    assert application.parent_population_before == 10
    assert application.child_population_after == len(application.reassigned_organism_ids)
    assert application.child_population_after == 5
    assert ecosystem.population("finch:g25") == 5
    assert ecosystem.population("finch") == 5
    assert runtime.lineage(ecosystem, "finch:g25") == ("finch", "finch:g25")


def test_speciation_rejects_population_size_that_is_not_observed() -> None:
    species = Species(
        species_id="hare",
        common_name="Hare",
        trophic_level=TrophicLevel.HERBIVORE,
        mature_age_ticks=2,
        max_age_ticks=20,
        reproduction_probability=0.8,
        movement_speed_mps=5.0,
    )
    ecosystem = Ecosystem()
    ecosystem.register_species(species)
    ecosystem.add_organism(Organism("h1", species, age_ticks=3))

    with pytest.raises(ValueError, match="observed live population"):
        EvolutionRuntime().apply_speciation(
            ecosystem,
            "hare",
            PopulationEnvironment(2, 0.9, 0.9, 0.1, 25),
        )


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
