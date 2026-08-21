import random

from genesis.life.ecosystem import Ecosystem
from genesis.life.genetics import Genome
from genesis.life.organism import Organism
from genesis.life.species import Species, TrophicLevel


def test_density_dependence_and_seeded_ecology_are_reproducible() -> None:
    species = Species(
        "mouse", "Mouse", TrophicLevel.HERBIVORE, 1, 100, 1.0, 5.0,
        carrying_capacity=20, reference_genome=Genome(body_mass_kg=0.03, speed_mps=5),
    )

    def run() -> tuple[int, tuple[str, ...]]:
        ecosystem = Ecosystem(seed=7)
        ecosystem.register_species(species)
        for index in range(4):
            ecosystem.add_organism(Organism(f"m{index}", species, age_ticks=2))
        ecosystem.step(3)
        return ecosystem.population("mouse"), tuple(sorted(ecosystem.organisms))

    assert run() == run()


def test_prey_filter_respects_species_diet() -> None:
    prey = Species("rabbit", "Rabbit", TrophicLevel.HERBIVORE, 1, 100, 0.1, 8)
    predator = Species("fox", "Fox", TrophicLevel.CARNIVORE, 1, 100, 0.1, 12, food_species=("rabbit",))
    ecosystem = Ecosystem()
    ecosystem.register_species(prey)
    ecosystem.register_species(predator)
    rabbit = Organism("r", prey)
    fox = Organism("f", predator)
    ecosystem.add_organism(rabbit)
    ecosystem.add_organism(fox)
    assert ecosystem.available_prey(fox) == (rabbit,)
