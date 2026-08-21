from __future__ import annotations

from genesis.agents.agent import Agent
from genesis.core.checkpoint import build_checkpoint
from genesis.core.config import SimulationConfig
from genesis.core.simulation import Simulation
from genesis.core.state import SimulationState
from genesis.demography.population import HumanLifeState
from genesis.events.event import SimulationEvent
from genesis.life.ecosystem import Ecosystem
from genesis.life.organism import Organism
from genesis.life.species import Species, TrophicLevel
from genesis.planet.coupling import PlanetEngine
from genesis.planet.terrain import TerrainCell, TerrainParams
from genesis.planet.water_cycle import PlanetaryWaterCycleEngine
from genesis.physics.vectors import Vec3
from genesis.settlement.settlements import Settlement


def test_simulation_seed_is_propagated_to_life_rng() -> None:
    first = Simulation(config=SimulationConfig(seed=101))
    second = Simulation(config=SimulationConfig(seed=202))

    assert first.state.ecosystem.seed == 101
    assert second.state.ecosystem.seed == 202


def test_checkpoint_contains_authoritative_life_state() -> None:
    simulation = Simulation(
        state=SimulationState(
            planet=PlanetEngine(TerrainParams(width=6, height=6, seed=5)),
            ecosystem=Ecosystem(seed=5),
        )
    )
    species = Species(
        "deer",
        "Deer",
        TrophicLevel.HERBIVORE,
        mature_age_ticks=2,
        max_age_ticks=100,
        reproduction_probability=0.1,
        movement_speed_mps=2.0,
        carrying_capacity=20,
    )
    simulation.state.ecosystem.register_species(species)
    simulation.state.ecosystem.add_organism(
        Organism("deer-1", species, position=Vec3(2.0, 0.0, 2.0), age_ticks=3)
    )
    simulation.add_agent(Agent("human", "Human"))
    simulation.step()

    life = build_checkpoint(simulation).payload["life"]
    assert life["species"][0]["species_id"] == "deer"
    assert life["organisms"][0]["organism_id"] == "deer-1"


def test_checkpoint_is_order_independent_for_event_mapping_data() -> None:
    first = Simulation(config=SimulationConfig(seed=1))
    second = Simulation(config=SimulationConfig(seed=1))
    first.add_agent(Agent("a", "A"))
    second.add_agent(Agent("a", "A"))
    first.emit(SimulationEvent(0, "Test", data={"b": {"y", "x"}, "a": 1}))
    second.emit(SimulationEvent(0, "Test", data={"a": 1, "b": {"x", "y"}}))

    assert build_checkpoint(first).digest == build_checkpoint(second).digest


def test_invariants_reject_reverse_identity_orphan_state() -> None:
    simulation = Simulation(config=SimulationConfig(seed=1))
    simulation.add_agent(Agent("a", "A"))
    simulation.state.demography.register(HumanLifeState("orphan"))
    report = simulation.validate()
    assert not report.ok
    assert any("demography identity mismatch" in item for item in report.violations)


def test_planetary_water_engine_does_not_leak_lake_storage_between_different_grids() -> None:
    lake = tuple(
        tuple(TerrainCell(x, y, 1.0 if (x, y) == (1, 1) else 2.0, True, 0.0) for x in range(4))
        for y in range(4)
    )
    flat = tuple(tuple(TerrainCell(x, y, 1.0, True, 0.0) for x in range(4)) for y in range(4))
    moisture = {(x, y): 1.0 for y in range(4) for x in range(4)}

    reused = PlanetaryWaterCycleEngine()
    reused.run(lake, tick=0, moisture_by_cell=moisture, soil_capacity_mm=0.0)
    leaked = reused.run(flat, tick=1, moisture_by_cell=moisture, soil_capacity_mm=0.0)
    fresh = PlanetaryWaterCycleEngine().run(flat, tick=1, moisture_by_cell=moisture, soil_capacity_mm=0.0)

    assert leaked.total_surface_storage_mm == fresh.total_surface_storage_mm


def test_external_surface_reservoir_is_reapplied_each_tick() -> None:
    ocean = tuple(tuple(TerrainCell(x, y, -100.0, False, 0.0) for x in range(4)) for y in range(4))
    supplied = {(x, y): 500.0 for y in range(4) for x in range(4)}
    moisture = {(x, y): 1.0 for y in range(4) for x in range(4)}
    engine = PlanetaryWaterCycleEngine()

    engine.run(ocean, tick=0, moisture_by_cell=moisture, surface_storage_by_cell=supplied, soil_capacity_mm=0.0)
    second = engine.run(ocean, tick=1, moisture_by_cell=moisture, surface_storage_by_cell=supplied, soil_capacity_mm=0.0)

    assert all(cell.surface_storage_mm == 500.0 for cell in second.cells)


def test_planet_engine_rejects_non_monotonic_stateful_ticks() -> None:
    engine = PlanetEngine(TerrainParams(width=6, height=6, seed=3))
    engine.step(1)
    try:
        engine.step(1)
    except ValueError:
        return
    raise AssertionError("stateful PlanetEngine accepted a duplicate tick")


def test_settlement_reverse_mapping_stays_consistent() -> None:
    simulation = Simulation(config=SimulationConfig(seed=2))
    simulation.add_agent(Agent("a", "A"))
    simulation.state.civilization.add_settlement(Settlement("s", "S", location=(1, 1)))
    simulation.state.civilization.assign_agent("a", "s")
    simulation.state.civilization.settlements["s"].population.clear()

    report = simulation.validate()
    assert not report.ok
    assert any("settlement mapping mismatch" in item for item in report.violations)
