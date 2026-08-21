from genesis.life.animal import Animal, AnimalEcology
from genesis.life.migration import HabitatConditions, MigrationProfile
from genesis.life.organism import Organism
from genesis.life.species import Species, TrophicLevel
from genesis.planet.migration_runtime import AnimalMigrationRuntime, DomesticationCoupler


def test_animal_migration_uses_environmental_suitability() -> None:
    species = Species(
        species_id="deer",
        common_name="Deer",
        trophic_level=TrophicLevel.HERBIVORE,
        mature_age_ticks=5,
        max_age_ticks=60,
        reproduction_probability=0.5,
        movement_speed_mps=4.0,
    )
    organism = Organism("deer-1", species)
    profile = MigrationProfile(
        species_id="deer",
        migratory=True,
        preferred_temperature_c=18,
        temperature_tolerance_c=12,
    )
    current = HabitatConditions(35, 5, 0.1, 0.2, 0.3)
    candidates = {
        "north": (HabitatConditions(20, 90, 0.9, 0.95, 0.8), 10.0, (4, 8)),
    }
    record = AnimalMigrationRuntime().evaluate(organism, profile, current, candidates)
    assert record is not None
    assert record.destination == (4, 8)


def test_human_positive_contact_changes_animal_response() -> None:
    animal = Animal("dog-1", AnimalEcology(species_id="dog"))
    before_fear = animal.ecology.human_fear
    DomesticationCoupler().apply_interaction(animal, positive=True)
    assert animal.ecology.human_fear < before_fear
    assert animal.bonded_to_human
