from random import Random

from genesis.life.genetics import Genome
from genesis.life.species import Species, TrophicLevel
from genesis.planet.atmosphere import AtmosphereEngine
from genesis.planet.biomes import BiomeEngine
from genesis.planet.ecology import FoodWeb
from genesis.planet.evolution import EvolutionEngine
from genesis.planet.hydrology import HydrologyEngine
from genesis.planet.migration import MigrationEngine
from genesis.planet.terrain import TerrainGenerator, TerrainParams


def test_terrain_is_deterministic_and_contains_land_and_ocean() -> None:
    params = TerrainParams(width=24, height=16, seed=42)
    a = TerrainGenerator(params).generate()
    b = TerrainGenerator(params).generate()
    assert a == b
    assert any(cell.land for row in a for cell in row)
    assert any(not cell.land for row in a for cell in row)


def test_hydrology_balances_water_routes_downstream_and_reaches_ocean_or_basin() -> None:
    engine = HydrologyEngine()
    state = engine.balance(
        rainfall_mm=100,
        temperature_c=22,
        humidity=0.65,
        wind_mps=4,
        soil_capacity_mm=30,
        surface_storage_mm=10,
    )
    assert state.runoff_mm >= 0
    assert state.infiltration_mm <= 30
    assert state.groundwater_mm <= state.infiltration_mm
    grid = TerrainGenerator(TerrainParams(width=8, height=8, seed=7)).generate()
    low = min((cell for row in grid for cell in row if cell.land), key=lambda c: c.elevation_m)
    downstream = engine.downhill_neighbor(grid, low.x, low.y)
    assert downstream is None or grid[downstream[1]][downstream[0]].elevation_m < low.elevation_m
    routes = engine.route_water(grid)
    assert len(routes) == 64
    assert all(route.path_length >= 0 for route in routes)
    assert any(route.terminal in {"ocean", "lake_or_watershed", "closed_depression"} for route in routes)


def test_atmosphere_and_biome_are_coupled() -> None:
    atmosphere = AtmosphereEngine().state(latitude=5, elevation_m=50, tick=100, moisture=0.9, ocean_fraction=0.7)
    biome = BiomeEngine().classify(
        temperature_c=atmosphere.temperature_c,
        precipitation_mm=atmosphere.precipitation_mm,
        elevation_m=50,
        soil_moisture=atmosphere.humidity,
    )
    assert atmosphere.pressure_kpa > 90
    assert 0 <= atmosphere.cloud_cover <= 1
    assert biome.vegetation_productivity > 0


def test_food_web_contains_terrestrial_and_aquatic_paths() -> None:
    web = FoodWeb()
    web.build_default_food_web()
    assert "plant" in web.prey_of("herbivore")
    assert "phytoplankton" in web.prey_of("zooplankton")
    assert web.energy_available(biomass=100, consumed=50, efficiency=0.1) == 5


def test_migration_responds_to_stress() -> None:
    intent = MigrationEngine().intent(
        organism_id="wolf-1",
        x=0,
        y=0,
        candidates=(
            {"x": 10, "y": 2, "food": 0.9, "water": 0.9, "climate_stress": 0.1, "reason": "water_and_prey"},
        ),
        temperature=35,
        preferred_temperature=18,
        water_need=1,
        local_water=0.1,
        food_need=1,
        local_food=0.2,
    )
    assert intent is not None
    assert intent.urgency > 0.2


def test_evolution_can_create_species_under_isolation() -> None:
    parent = Species(
        species_id="prey",
        common_name="Prey",
        trophic_level=TrophicLevel.HERBIVORE,
        mature_age_ticks=5,
        max_age_ticks=50,
        reproduction_probability=0.8,
        movement_speed_mps=2,
        carrying_capacity=100,
        reference_genome=Genome(),
    )
    result = EvolutionEngine().speciate(
        parent=parent,
        child_species_id="prey-island",
        isolation=0.9,
        environmental_distance=0.8,
        competition=0.2,
        generation=20,
        rng=Random(2),
    )
    assert result is not None
    child, event = result
    assert child.species_id == "prey-island"
    assert event.isolation == 0.9
