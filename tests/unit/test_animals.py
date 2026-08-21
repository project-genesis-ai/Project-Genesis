import pytest

from genesis.life.animal import Animal, AnimalEcology, AnimalPopulation, AnimalScale, AnimalStatus


def test_scales_cover_micro_to_megafauna() -> None:
    assert list(AnimalScale) == [AnimalScale.MICRO, AnimalScale.SMALL, AnimalScale.MEDIUM, AnimalScale.LARGE, AnimalScale.MEGAFAUNA]


def test_wild_domestic_and_stray_are_distinct_states() -> None:
    wild = Animal("w", AnimalEcology("wolf", AnimalStatus.WILD, AnimalScale.LARGE, aggression=0.8, habitat_range_km2=100.0))
    domestic = Animal("d", AnimalEcology("dog", AnimalStatus.DOMESTIC, AnimalScale.MEDIUM, human_fear=0.1, human_trust=0.9, aggression=0.2, domestication=0.9))
    stray = Animal("s", AnimalEcology("dog", AnimalStatus.STRAY, AnimalScale.MEDIUM, human_fear=0.5, human_trust=0.2, aggression=0.5, domestication=0.4))
    assert wild.danger_to_human > domestic.danger_to_human
    assert stray.danger_to_human > domestic.danger_to_human


def test_positive_human_interaction_builds_trust() -> None:
    animal = Animal("dog", AnimalEcology("dog", AnimalStatus.STRAY, human_fear=0.6, human_trust=0.1, domestication=0.5))
    animal.encounter_human(positive_interaction=True)
    assert animal.ecology.human_fear == pytest.approx(0.55)
    assert animal.ecology.human_trust == pytest.approx(0.15)
    assert animal.bonded_to_human


def test_population_can_measure_wildlife_danger() -> None:
    animals = AnimalPopulation({
        "a": Animal("a", AnimalEcology("mouse", AnimalStatus.WILD, AnimalScale.SMALL, aggression=0.01)),
        "b": Animal("b", AnimalEcology("tiger", AnimalStatus.WILD, AnimalScale.MEGAFAUNA, aggression=0.9, human_fear=0.8, habitat_range_km2=500.0)),
    })
    assert animals.danger_index() > 0.0
    assert len(animals.by_status(AnimalStatus.WILD)) == 2


def test_invalid_domestic_animal_is_rejected() -> None:
    with pytest.raises(ValueError):
        AnimalEcology("dog", AnimalStatus.DOMESTIC, domestication=0.0)
