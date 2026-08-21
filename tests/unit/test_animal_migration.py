import pytest

from genesis.life import (
    Animal,
    AnimalEcology,
    AnimalPopulation,
    AnimalScale,
    AnimalStatus,
    HabitatConditions,
    MigrationProfile,
    decide_migration,
    habitat_suitability,
)


def test_wild_domestic_and_stray_are_distinct() -> None:
    wild = Animal("w", AnimalEcology("wolf", AnimalStatus.WILD, AnimalScale.LARGE, aggression=0.8))
    domestic = Animal("d", AnimalEcology("dog", AnimalStatus.DOMESTIC, AnimalScale.MEDIUM, domestication=1.0, human_trust=0.8))
    stray = Animal("s", AnimalEcology("dog", AnimalStatus.STRAY, AnimalScale.MEDIUM, human_trust=0.2))
    population = AnimalPopulation({a.animal_id: a for a in (wild, domestic, stray)})
    assert len(population.by_status(AnimalStatus.WILD)) == 1
    assert domestic.danger_to_human < wild.danger_to_human
    assert population.danger_index() > 0


def test_positive_human_encounter_increases_trust() -> None:
    animal = Animal("dog", AnimalEcology("dog", AnimalStatus.STRAY, domestication=0.4, human_fear=0.8))
    animal.encounter_human(positive_interaction=True)
    assert animal.ecology.human_trust == pytest.approx(0.05)
    assert animal.ecology.human_fear == pytest.approx(0.75)
    assert animal.bonded_to_human


def test_migratory_species_moves_toward_better_seasonal_habitat() -> None:
    profile = MigrationProfile("caribou", True, preferred_temperature_c=5.0, temperature_tolerance_c=15.0, maximum_daily_distance_km=100.0)
    current = HabitatConditions(30.0, 10.0, 0.8, 0.2, 0.7)
    northern = HabitatConditions(6.0, 20.0, 0.9, 0.9, 0.8)
    decision = decide_migration(profile, current, {"north": (northern, 80.0)})
    assert decision.should_migrate
    assert decision.destination_id == "north"
    assert decision.suitability_destination > decision.suitability_current


def test_non_migratory_species_stays_even_if_other_habitat_is_better() -> None:
    profile = MigrationProfile("bear", False, preferred_temperature_c=10.0, temperature_tolerance_c=20.0)
    current = HabitatConditions(30.0, 5.0, 0.5, 0.2, 0.5)
    destination = HabitatConditions(10.0, 30.0, 0.9, 0.9, 0.9)
    decision = decide_migration(profile, current, {"better": (destination, 10.0)})
    assert not decision.should_migrate
    assert decision.destination_id is None


def test_migration_respects_food_water_and_daily_distance() -> None:
    profile = MigrationProfile("bird", True, 15.0, 10.0, minimum_food=0.4, minimum_water=0.4, maximum_daily_distance_km=50.0)
    current = HabitatConditions(30.0, 5.0, 0.5, 0.3, 0.5)
    too_far = HabitatConditions(15.0, 30.0, 0.9, 0.9, 0.9)
    too_dry = HabitatConditions(15.0, 30.0, 0.2, 0.9, 0.9)
    decision = decide_migration(profile, current, {"far": (too_far, 100.0), "dry": (too_dry, 20.0)})
    assert not decision.should_migrate


def test_habitat_suitability_is_bounded() -> None:
    profile = MigrationProfile("elk", True, 8.0, 12.0)
    conditions = HabitatConditions(8.0, 100.0, 1.0, 1.0, 1.0)
    assert 0.0 <= habitat_suitability(profile, conditions) <= 1.0
