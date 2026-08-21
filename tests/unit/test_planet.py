from genesis.world.planet import Atmosphere, GravityField, OceanWater, Planet, PlanetCell, SpaceEnvironment, Terrain


def test_default_earth_like_land_is_breathable() -> None:
    cell = PlanetCell("land", Terrain.PLAINS)
    assert cell.human_can_breathe
    assert 20.0 <= cell.atmosphere.oxygen_fraction * 100.0 <= 22.0


def test_factory_pollution_changes_local_air() -> None:
    cell = PlanetCell("factory", Terrain.PLAINS)
    original_oxygen = cell.atmosphere.oxygen_fraction
    original_co2 = cell.atmosphere.carbon_dioxide_ppm
    cell.apply_factory_emissions(100.0)
    assert cell.atmosphere.oxygen_fraction < original_oxygen
    assert cell.atmosphere.carbon_dioxide_ppm > original_co2
    assert cell.atmosphere.pollutants_index > 0.0


def test_tree_cover_supports_local_oxygen_recovery() -> None:
    cell = PlanetCell("forest", Terrain.FOREST, tree_cover=0.8)
    before = cell.atmosphere.oxygen_fraction
    cell.apply_tree_exchange(0.1)
    assert cell.atmosphere.oxygen_fraction >= before
    assert cell.tree_cover == 0.9


def test_ocean_supports_fish_but_not_human_breathing() -> None:
    water = OceanWater(dissolved_oxygen_mg_l=7.5)
    ocean = PlanetCell("sea", Terrain.OCEAN, ocean=water)
    assert ocean.ocean is not None
    assert ocean.ocean.supports_fish
    assert not ocean.human_can_breathe
    assert not ocean.ocean.supports_human_breathing


def test_space_has_no_breathable_air() -> None:
    space = SpaceEnvironment()
    assert not space.human_can_breathe
    assert not space.fish_can_live


def test_gravity_falls_with_altitude() -> None:
    gravity = GravityField()
    assert gravity.acceleration(0.0) == gravity.surface_g
    assert gravity.acceleration(10_000.0) < gravity.surface_g


def test_wildlife_risk_increases_with_wildlife_and_forest_cover() -> None:
    open_land = PlanetCell("open", Terrain.PLAINS, tree_cover=0.1, wild_animal_pressure=0.5)
    jungle = PlanetCell("jungle", Terrain.FOREST, tree_cover=0.9, wild_animal_pressure=0.5)
    assert jungle.human_wildlife_risk > open_land.human_wildlife_risk


def test_planet_can_hold_large_mixed_world() -> None:
    planet = Planet()
    planet.add_cell(PlanetCell("continent_a", Terrain.FOREST, elevation_m=300.0, tree_cover=0.8))
    planet.add_cell(PlanetCell("continent_b", Terrain.DESERT, elevation_m=500.0))
    planet.add_cell(PlanetCell("ocean_1", Terrain.OCEAN))
    assert len(planet.cells) == 3
    assert planet.cell("ocean_1").environment_type.value == "ocean"


def test_atmosphere_validates_physical_ranges() -> None:
    assert Atmosphere().oxygen_partial_pressure_kpa > 0
