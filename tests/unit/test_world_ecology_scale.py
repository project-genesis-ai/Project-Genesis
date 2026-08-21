from genesis.life.behavior import EcologicalBehavior
from genesis.life.ecosystem import Ecosystem
from genesis.life.food_web import FoodWeb
from genesis.life.habitat import HabitatCell, HabitatMap
from genesis.life.organism import Organism
from genesis.life.population import PopulationDynamics
from genesis.life.species import Species, TrophicLevel
from genesis.physics.vectors import Vec3
from genesis.world.climate import ClimateCell, ClimateModel
from genesis.world.environment import Biome, Environment, EnvironmentCell


def make_species(species_id: str, level: TrophicLevel, **kwargs) -> Species:
    return Species(
        species_id,
        species_id.title(),
        level,
        mature_age_ticks=2,
        max_age_ticks=100,
        reproduction_probability=kwargs.get("reproduction_probability", 0.0),
        movement_speed_mps=kwargs.get("movement_speed_mps", 1.0),
        food_species=kwargs.get("food_species", ()),
        carrying_capacity=kwargs.get("carrying_capacity", 100),
    )


def test_climate_is_deterministic_and_bounded() -> None:
    first = ClimateCell()
    second = ClimateCell()
    model = ClimateModel()
    model.step(first, 90)
    model.step(second, 90)
    assert first == second
    assert 0.0 <= first.humidity <= 1.0
    assert first.precipitation_mm >= 0.0


def test_habitat_neighbors_are_spatially_sorted() -> None:
    habitat = HabitatMap()
    habitat.add(HabitatCell("a", 0, 0))
    habitat.add(HabitatCell("b", 1, 0))
    habitat.add(HabitatCell("c", 0, 1))
    assert [cell.cell_id for cell in habitat.neighbors(0, 0)] == ["b", "c"]


def test_herbivore_forage_reduces_vegetation_and_adds_energy() -> None:
    habitat = HabitatMap()
    habitat.add(HabitatCell("forest", 0, 0, vegetation=1.0))
    herbivore = Organism("deer-1", make_species("deer", TrophicLevel.HERBIVORE), position=Vec3())
    result = EcologicalBehavior(seed=7).forage(herbivore, habitat)
    assert result.action == "graze"
    assert result.resource > 0.0
    assert herbivore.energy == 1.0
    assert habitat.get(0, 0).vegetation < 1.0


def test_food_web_transfers_energy_and_kills_prey() -> None:
    grass = make_species("grass", TrophicLevel.PRODUCER)
    wolf = make_species("wolf", TrophicLevel.CARNIVORE, food_species=("deer",))
    deer = make_species("deer", TrophicLevel.HERBIVORE)
    ecosystem = Ecosystem()
    for species in (grass, wolf, deer):
        ecosystem.register_species(species)
    predator = Organism("wolf-1", wolf, energy=0.5)
    prey = Organism("deer-1", deer, energy=1.0)
    ecosystem.add_organism(predator)
    ecosystem.add_organism(prey)
    result = FoodWeb(0.2).feed(predator, prey)
    assert result is not None
    assert not prey.alive
    assert predator.energy == 0.7


def test_population_reproduces_deterministically() -> None:
    species = make_species("deer", TrophicLevel.HERBIVORE, reproduction_probability=1.0, carrying_capacity=3)
    ecosystem = Ecosystem()
    ecosystem.register_species(species)
    parent = Organism("deer-1", species, age_ticks=10, energy=1.0)
    ecosystem.add_organism(parent)
    newborns = PopulationDynamics(seed=1).step(ecosystem)
    assert len(newborns) == 1
    assert ecosystem.population("deer") == 2
    assert newborns[0].position == parent.position


def test_environment_climate_updates_environment_cell() -> None:
    environment = Environment()
    environment.add_cell(EnvironmentCell("c1", Biome.FOREST))
    environment.step_climate(100)
    assert environment.cell("c1").temperature_c == environment.climate["c1"].temperature_c
    assert environment.cell("c1").rainfall_mm >= 0.0
