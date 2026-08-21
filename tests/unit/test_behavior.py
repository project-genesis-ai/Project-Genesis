import pytest

from genesis.life.behavior import EcologicalBehavior
from genesis.life.habitat import HabitatCell, HabitatMap
from genesis.life.organism import Organism
from genesis.life.species import Species, TrophicLevel


def make_species(probability: float = 0.5) -> Species:
    return Species(
        species_id="deer",
        common_name="Deer",
        trophic_level=TrophicLevel.HERBIVORE,
        mature_age_ticks=5,
        max_age_ticks=100,
        reproduction_probability=probability,
        movement_speed_mps=2.0,
    )


def make_habitat(vegetation: float = 1.0, water: float = 1.0) -> HabitatMap:
    habitat = HabitatMap()
    habitat.add(HabitatCell("home", 0, 0, vegetation=vegetation, water=water))
    return habitat


def test_decision_responds_to_energy_and_resources() -> None:
    organism = Organism("deer-1", make_species(), energy=0.2)
    result = EcologicalBehavior(seed=7).decide(organism, make_habitat())
    assert result.action == "forage"
    assert organism.memory["decision_count"] == 1.0


def test_act_feeds_back_resource_success_into_memory() -> None:
    organism = Organism("deer-1", make_species(), energy=0.2)
    result = EcologicalBehavior(seed=7).act(organism, make_habitat())
    assert result.action == "graze"
    assert result.resource > 0.0
    assert 0.0 <= organism.memory["graze"] <= 1.0
    assert 0.0 <= organism.energy <= 1.0


def test_behavior_is_order_independent_for_reproduction_roll() -> None:
    behavior = EcologicalBehavior(seed=42)
    first = Organism("a", make_species(0.5), age_ticks=10, energy=0.9)
    second = Organism("b", make_species(0.5), age_ticks=10, energy=0.9)
    assert behavior.should_reproduce(first) == behavior.should_reproduce(first)
    assert behavior.should_reproduce(second) == behavior.should_reproduce(second)


def test_dead_organism_cannot_choose_survival_action() -> None:
    organism = Organism("dead", make_species())
    organism.die()
    assert EcologicalBehavior().decide(organism, make_habitat()).action == "dead"


def test_negative_reproduction_probability_is_rejected_by_species() -> None:
    with pytest.raises(ValueError):
        make_species(-0.1)
