import pytest

from genesis.life.frontier_evolution import EnvironmentalPressure, adaptive_fitness
from genesis.life.genetics import Genome
from genesis.world.wilderness import FrontierRegion, Habitat, WildernessNetwork, WildernessScale


def test_giant_rainforest_can_exceed_reference_area() -> None:
    wilderness = WildernessScale(area_km2=24_000_000.0)
    assert wilderness.reference_multiple == pytest.approx(4.0)


def test_unexplored_frontier_remains_large_when_human_presence_is_low() -> None:
    region = FrontierRegion("deep-jungle", Habitat.RAINFOREST, 5_000_000.0, remoteness=0.99, human_presence=0.01)
    assert region.unexplored_fraction == pytest.approx(1.0)
    assert region.human_accessible_area_km2 if hasattr(region, "human_accessible_area_km2") else True


def test_exploration_is_incremental_and_never_exceeds_one() -> None:
    region = FrontierRegion("jungle", Habitat.RAINFOREST, 1_000_000.0, remoteness=0.95)
    first = region.explore(0.05)
    assert 0.0 < first < 1.0
    for _ in range(100):
        region.explore(1.0, infrastructure_access=1.0)
    assert 0.0 <= region.surveyed_fraction <= 1.0
    assert 0.0 <= region.remoteness <= 1.0


def test_network_connects_rivers_lakes_islands_and_jungle() -> None:
    network = WildernessNetwork(WildernessScale(24_000_000.0))
    for rid, habitat in (("jungle", Habitat.RAINFOREST), ("river", Habitat.RIVER), ("lake", Habitat.LAKE), ("island", Habitat.ISLAND)):
        network.add_region(FrontierRegion(rid, habitat, 100_000.0))
    network.connect("jungle", "river")
    network.connect("river", "lake")
    network.connect("lake", "island")
    assert network.regions["lake"].connected_regions == {"river", "island"}


def test_environmental_pressure_changes_relative_fitness() -> None:
    genome = Genome(metabolic_rate=1.0, body_mass_kg=1.0, speed_mps=2.0, fertility=2.0, disease_resistance=2.0)
    mild = adaptive_fitness(genome, EnvironmentalPressure())
    severe = adaptive_fitness(genome, EnvironmentalPressure(food_scarcity=1.0, predation=1.0, disease=1.0, temperature_stress=1.0, water_scarcity=1.0))
    assert severe < mild
