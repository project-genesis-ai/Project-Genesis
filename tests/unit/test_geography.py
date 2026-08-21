from genesis.geography import Biome, ClimateEngine, GeoCell, Geography, ResourceField, ResourceStock


def test_sparse_geography_neighbors_are_deterministic() -> None:
    world = Geography()
    world.add(GeoCell(0, 0, 100, 10, Biome.FOREST, 0.7, 1.0))
    world.add(GeoCell(1, 0, 90, 10, Biome.PLAINS, 0.5, 0.8))
    world.add(GeoCell(0, 2, 120, 11, Biome.FOREST, 0.6, 0.9))
    assert [(c.x, c.y) for c in world.neighbors(0, 0)] == [(1, 0)]
    assert [(c.x, c.y) for c in world.neighbors(0, 0, 2)] == [(0, 2), (1, 0)]


def test_climate_is_seedless_and_reproducible() -> None:
    engine = ClimateEngine()
    first = engine.state(latitude=20, elevation_m=100, tick=42, moisture=0.6)
    second = engine.state(latitude=20, elevation_m=100, tick=42, moisture=0.6)
    assert first == second
    assert first.precipitation_mm >= 0


def test_resource_harvest_and_regeneration_are_bounded() -> None:
    stock = ResourceStock(amount=10, capacity=12, regeneration_per_tick=1)
    assert stock.harvest(7) == 7
    stock.regenerate(5)
    assert stock.amount == 8
    assert stock.harvest(100) == 8
    assert stock.amount == 0
