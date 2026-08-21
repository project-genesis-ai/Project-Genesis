from genesis.life.ecosystem import Ecosystem
from genesis.life.genetics import Genome
from genesis.life.organism import Organism
from genesis.life.population import PopulationDynamics
from genesis.life.species import Species, TrophicLevel
from genesis.life.systems import LifeSystem


def make_species(species_id: str = "herbivore", capacity: int = 10) -> Species:
    return Species(
        species_id=species_id,
        common_name=species_id,
        trophic_level=TrophicLevel.HERBIVORE,
        mature_age_ticks=1,
        max_age_ticks=100,
        reproduction_probability=1.0,
        movement_speed_mps=1.0,
        carrying_capacity=capacity,
        reference_genome=Genome(fertility=1.0),
    )


def test_ecosystem_is_the_single_reproduction_authority_for_life_system():
    ecosystem = Ecosystem(seed=17)
    species = make_species()
    ecosystem.register_species(species)
    ecosystem.add_organism(Organism("a", species, age_ticks=2))
    ecosystem.add_organism(Organism("b", species, age_ticks=2))

    ecosystem.step(1)
    count_after_ecosystem = len(ecosystem.organisms)
    PopulationDynamics(seed=17).step(ecosystem, 1, reproduce=False)

    assert len(ecosystem.organisms) == count_after_ecosystem
    assert count_after_ecosystem >= 2


def test_disease_transmission_is_deterministic_and_affects_host():
    ecosystem = Ecosystem(seed=23)
    species = make_species()
    ecosystem.register_species(species)
    host = Organism("host", species, energy=1.0)
    susceptible = Organism("susceptible", species, energy=1.0)
    ecosystem.add_organism(host)
    ecosystem.add_organism(susceptible)

    life = LifeSystem(infection_clearance_rate=0.0)
    life.seed_infection("host", pathogen_id="p", load=1.0, transmissibility=1.0, damage=0.1)
    life._advance_disease(ecosystem, seed=23)

    assert host.energy == 0.9
    assert "susceptible" in life.infections
    assert life.last_infections[0].host_id == "susceptible"


def test_disease_parameters_are_validated():
    life = LifeSystem()
    try:
        life.seed_infection("host", load=-1.0)
    except ValueError:
        pass
    else:
        raise AssertionError("negative infection load must be rejected")
