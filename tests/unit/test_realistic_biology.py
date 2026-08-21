import random

import pytest

from genesis.life.genetics import Genome
from genesis.life.organism import Organism
from genesis.life.physiology import Physiology
from genesis.life.species import Species, TrophicLevel


def species() -> Species:
    return Species(
        species_id="deer", common_name="Deer", trophic_level=TrophicLevel.HERBIVORE,
        mature_age_ticks=10, max_age_ticks=100, reproduction_probability=1.0,
        movement_speed_mps=12.0, carrying_capacity=100,
        reference_genome=Genome(body_mass_kg=70.0, speed_mps=12.0),
    )


def test_allometric_metabolism_is_sublinear_with_mass() -> None:
    light = Physiology(1.0).basal_power_watts
    heavy = Physiology(100.0).basal_power_watts
    assert heavy / light == pytest.approx(100.0 ** 0.75)
    assert heavy / light < 100.0


def test_genome_inheritance_is_reproducible() -> None:
    a = Genome(body_mass_kg=70, speed_mps=10)
    b = Genome(body_mass_kg=80, speed_mps=12)
    one = Genome.inherit(a, b, random.Random(42))
    two = Genome.inherit(a, b, random.Random(42))
    assert one == two


def test_reproduction_requires_mature_same_species() -> None:
    s = species()
    parent = Organism("a", s, age_ticks=20)
    immature = Organism("b", s, age_ticks=1)
    assert parent.reproduce(immature, "c", random.Random(1)) is None


def test_reproduction_inherits_genome() -> None:
    s = species()
    a = Organism("a", s, age_ticks=20, genome=Genome(body_mass_kg=70))
    b = Organism("b", s, age_ticks=20, genome=Genome(body_mass_kg=80))
    child = a.reproduce(b, "c", random.Random(1))
    assert child is not None
    assert 60 < child.genome.body_mass_kg < 90
