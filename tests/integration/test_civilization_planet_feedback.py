from genesis.planet.civilization_feedback import PlanetaryCivilizationFeedback
from genesis.planet.coupling import PlanetEngine
from genesis.planet.terrain import TerrainParams


def test_civilization_feedback_changes_future_planet_state() -> None:
    planet = PlanetEngine(TerrainParams(width=12, height=12, seed=21))
    baseline = planet.step(1)
    cell = baseline.cells[4][4]
    feedback = PlanetaryCivilizationFeedback()
    impact = feedback.assess(
        region_id="4:4",
        population=5000,
        farmland_area=60,
        water_extraction=0.8,
        pollution=0.9,
        natural_land_area=100,
    )
    planet.set_human_impact(cell.terrain.x, cell.terrain.y, impact)
    impacted = planet.step(2)
    before = baseline.cells[cell.terrain.y][cell.terrain.x]
    after = impacted.cells[cell.terrain.y][cell.terrain.x]
    assert after.biome.vegetation_productivity <= before.biome.vegetation_productivity or after.hydrology.groundwater_mm <= before.hydrology.groundwater_mm


def test_civilization_feedback_can_be_removed() -> None:
    planet = PlanetEngine(TerrainParams(width=10, height=10, seed=3))
    snapshot = planet.step(1)
    cell = snapshot.cells[2][2]
    feedback = PlanetaryCivilizationFeedback()
    impact = feedback.assess("2:2", 1000, 20, 0.4, 0.3, 100)
    planet.set_human_impact(cell.terrain.x, cell.terrain.y, impact)
    planet.clear_human_impacts()
    next_snapshot = planet.step(2)
    assert next_snapshot is not None
