from genesis.core.config import SimulationConfig
from genesis.core.simulation import Simulation
from genesis.life.ecosystem import Ecosystem
from genesis.life.genetics import Genome
from genesis.life.organism import Organism
from genesis.life.species import Species, TrophicLevel


def test_ecosystem_selection_path_is_deterministic():
    def build():
        ecosystem = Ecosystem(seed=31)
        species = Species(
            "grazers", "grazers", TrophicLevel.HERBIVORE,
            mature_age_ticks=1, max_age_ticks=100,
            reproduction_probability=1.0, movement_speed_mps=1.0,
            carrying_capacity=20, reference_genome=Genome(fertility=1.0),
        )
        ecosystem.register_species(species)
        ecosystem.add_organism(Organism("a", species, age_ticks=2, energy=1.0))
        ecosystem.add_organism(Organism("b", species, age_ticks=2, energy=0.8))
        return ecosystem

    left = build()
    right = build()
    left.step(1)
    right.step(1)
    assert sorted(left.organisms) == sorted(right.organisms)
    assert [left.organisms[k].genome.fitness for k in sorted(left.organisms)] == [right.organisms[k].genome.fitness for k in sorted(right.organisms)]


def test_simulation_smoke_still_advances_after_life_integration():
    simulation = Simulation(config=SimulationConfig(seed=41))
    first = simulation.step().tick
    second = simulation.step().tick
    assert second > first
    assert simulation.validate().ok
