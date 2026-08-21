from genesis.biology.dynamics import BiologicalDynamics, InfectionState
from genesis.life.ecosystem import Ecosystem
from genesis.life.genetics import Genome
from genesis.life.organism import Organism
from genesis.life.species import Species, TrophicLevel
from genesis.life.systems import LifeSystem


def test_life_organism_disease_feedback_does_not_cross_universal_biology_model_boundary():
    ecosystem = Ecosystem(seed=101)
    species = Species(
        "host", "host", TrophicLevel.HERBIVORE,
        mature_age_ticks=1, max_age_ticks=100,
        reproduction_probability=1.0, movement_speed_mps=1.0,
        carrying_capacity=10, reference_genome=Genome(fertility=1.0),
    )
    ecosystem.register_species(species)
    host = Organism("host-1", species, energy=1.0, health=1.0)
    ecosystem.add_organism(host)

    life = LifeSystem(infection_clearance_rate=0.0)
    life.seed_infection("host-1", load=1.0, transmissibility=0.0, damage=0.2)
    life._advance_disease(ecosystem, seed=101)

    assert host.energy == 0.8
    assert host.health == 0.8

    universal = type("UniversalHost", (), {})()
    universal.identity = type("Identity", (), {"identity_id": "host-1"})()
    universal.internal = type("Internal", (), {"energy": 1.0, "stress": 0.0, "clamp": lambda self: None})()
    BiologicalDynamics.apply_infection(universal, InfectionState("p", "host-1", 1.0, 0.0, 0.2))
    assert universal.internal.energy == 0.8
