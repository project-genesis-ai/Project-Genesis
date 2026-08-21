from genesis.life.evolution import EvolutionRuntime
from genesis.life.genetics import Genome
from genesis.life.organism import Organism
from genesis.life.species import Species


def _organism(identifier: str, genome: Genome | None = None) -> Organism:
    species = Species(
        species_id="species:test",
        name="Test Species",
        reference_genome=genome or Genome(),
        max_age_ticks=100,
        mature_age_ticks=10,
        reproduction_probability=0.5,
    )
    return Organism(identifier, species, genome=genome or species.reference_genome)


def test_evolution_fitness_is_bounded_and_deterministic() -> None:
    organism = _organism("a")
    runtime = EvolutionRuntime()

    first = runtime.evaluate([organism], {"species:test": 0.4}, seed=99)
    second = runtime.evaluate([organism], {"species:test": 0.4}, seed=99)

    assert first == second
    assert 0.0 <= first[0].fitness <= 1.0
    assert 0.0 <= first[0].survival_probability <= 1.0
    assert organism.alive


def test_genome_distance_and_ancestry_are_stable() -> None:
    runtime = EvolutionRuntime()
    parent_a = _organism("parent-a", Genome(body_mass_kg=1.0, speed_mps=1.0))
    parent_b = _organism("parent-b", Genome(body_mass_kg=2.0, speed_mps=1.5))
    child = _organism("child", Genome(body_mass_kg=1.5, speed_mps=1.2))

    runtime.register(parent_a)
    runtime.register(parent_b)
    runtime.register(child, ("parent-a", "parent-b"))

    assert runtime.lineage["child"].generation == 1
    assert runtime.ancestry("child") == ("parent-a", "parent-b")
    assert runtime.genome_distance("parent-a", "parent-b") > 0.0
