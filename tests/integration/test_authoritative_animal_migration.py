from genesis.life.ecosystem import Ecosystem
from genesis.life.migration import MigrationProfile
from genesis.life.organism import Organism
from genesis.life.species import Species, TrophicLevel
from genesis.life.systems import LifeSystem
from genesis.world.environment import Biome, Environment, EnvironmentCell


def test_authoritative_life_tick_moves_migratory_species_to_better_habitat() -> None:
    species = Species(
        species_id="deer",
        common_name="Deer",
        trophic_level=TrophicLevel.HERBIVORE,
        mature_age_ticks=2,
        max_age_ticks=100,
        reproduction_probability=0.0,
        movement_speed_mps=2.0,
        migration_profile=MigrationProfile(
            species_id="deer",
            migratory=True,
            preferred_temperature_c=18.0,
            temperature_tolerance_c=10.0,
            minimum_food=0.25,
            minimum_water=0.25,
            maximum_daily_distance_km=2.0,
        ),
    )
    ecosystem = Ecosystem()
    ecosystem.register_species(species)
    organism = Organism("deer-1", species)
    ecosystem.add_organism(organism)

    environment = Environment()
    environment.add_cell(EnvironmentCell("0:0", Biome.DESERT, temperature_c=35.0, rainfall_mm=5.0, water_mm=5.0, vegetation=0.1, x=0, y=0))
    environment.add_cell(EnvironmentCell("1:0", Biome.GRASSLAND, temperature_c=18.0, rainfall_mm=90.0, water_mm=90.0, vegetation=0.9, x=1, y=0))

    life = LifeSystem()
    # A planet snapshot is required to activate the authoritative migration path.
    class Snapshot:  # structural test double; only presence matters for this path
        pass

    life.step(environment, ecosystem, ticks=1, planet_snapshot=Snapshot())

    assert organism.position.x == 1.0
    assert organism.position.z == 0.0
    assert len(life.last_migrations) == 1
