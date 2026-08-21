import random

from genesis.life.genetics import Genome


def test_genome_fitness_is_deterministic() -> None:
    genome = Genome(metabolic_rate=1.0, body_mass_kg=2.0, speed_mps=1.0, fertility=2.0, disease_resistance=3.0)
    assert genome.fitness == 6.0


def test_inheritance_is_seed_reproducible_and_bounded() -> None:
    a = Genome(body_mass_kg=2.0, speed_mps=3.0, fertility=2.0, disease_resistance=2.0)
    b = Genome(body_mass_kg=4.0, speed_mps=1.0, fertility=1.0, disease_resistance=4.0)
    first = Genome.inherit(a, b, random.Random(42), mutation_sigma=0.01)
    second = Genome.inherit(a, b, random.Random(42), mutation_sigma=0.01)
    assert first == second
    assert first.body_mass_kg > 0.0
    assert first.metabolic_rate > 0.0
