import importlib

import genesis.planet as planet
from genesis.planet.terrain import TerrainParams


def test_planet_public_exports_are_importable() -> None:
    for name in planet.__all__:
        assert hasattr(planet, name), f"missing public export: {name}"


def test_planet_engine_survives_multiple_ticks_with_cached_topology() -> None:
    engine = planet.PlanetEngine(TerrainParams(width=8, height=8, seed=17))

    first = engine.step(1)
    second = engine.step(2)
    third = engine.step(3)

    assert first.topology is second.topology is third.topology
    assert first.routes is second.routes is third.routes
    assert len(first.cells) == 8
    assert all(len(row) == 8 for row in first.cells)
    assert len(first.rivers.segments) == 64
    assert len(second.rivers.segments) == 64
    assert len(third.rivers.segments) == 64


def test_planet_runtime_module_is_the_canonical_runtime_location() -> None:
    runtime_module = importlib.import_module("genesis.planet.runtime")
    assert runtime_module.PlanetEcologyRuntime is planet.PlanetEcologyRuntime
