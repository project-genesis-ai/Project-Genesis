from genesis.core.config import SimulationConfig
from genesis.core.simulation import Simulation
from genesis.life.genetics import Genome
from genesis.life.organism import Organism
from genesis.life.species import Species, TrophicLevel


def _species() -> Species:
    return Species(
        "bio-wolf",
        "Bio Wolf",
        TrophicLevel.CARNIVORE,
        1,
        100,
        1.0,
        5.0,
        carrying_capacity=20,
        reproduction_probability=1.0,
        reference_genome=Genome(body_mass_kg=20.0, speed_mps=10.0),
    )


def test_universal_biology_is_executed_inside_authoritative_life_runtime():
    simulation = Simulation(config=SimulationConfig(seed=31))
    species = _species()
    simulation.state.ecosystem.register_species(species)
    simulation.state.ecosystem.add_organism(Organism("bio-a", species, age_ticks=2))
    simulation.state.ecosystem.add_organism(Organism("bio-b", species, age_ticks=2))

    simulation.step()

    biological = simulation.life.last_biological_step
    assert {item.organism_id for item in biological.actions} == {"bio-a", "bio-b"}
    assert all(item.action for item in biological.actions)
    assert any(key.startswith("universal:") for key in simulation.state.ecosystem.organisms["bio-a"].memory)
    assert simulation.state.ecosystem.population("bio-wolf") >= 2
    assert simulation.validate().ok


def test_biology_reproduction_is_seeded_by_authoritative_ecosystem_seed():
    def run() -> tuple[int, tuple[str, ...]]:
        simulation = Simulation(config=SimulationConfig(seed=41))
        species = _species()
        simulation.state.ecosystem.register_species(species)
        simulation.state.ecosystem.add_organism(Organism("bio-a", species, age_ticks=2))
        simulation.state.ecosystem.add_organism(Organism("bio-b", species, age_ticks=2))
        simulation.step()
        return simulation.state.ecosystem.population("bio-wolf"), tuple(sorted(simulation.state.ecosystem.organisms))

    assert run() == run()
