import pytest

from genesis.life.ecosystem import Ecosystem
from genesis.life.forest import ForestDynamics
from genesis.life.organism import Organism
from genesis.life.species_presets import forest_species
from genesis.world.environment import Biome, EnvironmentCell


def test_forest_food_chain_and_population() -> None:
    ecosystem = Ecosystem()
    oak, deer, tiger = forest_species()
    for species in (oak, deer, tiger):
        ecosystem.register_species(species)

    deer_one = Organism("deer-1", deer)
    tiger_one = Organism("tiger-1", tiger)
    ecosystem.add_organism(deer_one)
    ecosystem.add_organism(tiger_one)

    assert ecosystem.population("deer") == 1
    assert ecosystem.available_prey(tiger_one) == (deer_one,)


def test_ecosystem_rejects_unregistered_species() -> None:
    ecosystem = Ecosystem()
    deer = forest_species()[1]
    with pytest.raises(ValueError):
        ecosystem.add_organism(Organism("deer-1", deer))


def test_forest_growth_uses_water_and_temperature() -> None:
    cell = EnvironmentCell("forest-1", Biome.FOREST, temperature_c=24.0, water_mm=10.0, vegetation=0.2)
    ForestDynamics().step(cell, ticks=10)
    assert cell.vegetation > 0.2
    assert cell.water_mm < 10.0
