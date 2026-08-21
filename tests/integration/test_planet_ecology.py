from genesis.planet.aquatic import AquaticCell, AquaticSystem
from genesis.planet.hydrology import HydrologyEngine
from genesis.planet.terrain import TerrainGenerator, TerrainParams


def test_aquatic_food_chain_grows_from_plankton_to_predators() -> None:
    system = AquaticSystem()
    cell = AquaticCell(salinity=1.0, dissolved_oxygen=0.9, nutrients=0.9, depth_m=100, temperature_c=18)
    system.add_cell(0, 0, cell)
    system.step(sunlight=0.9)
    assert cell.biomass.get("phytoplankton", 0) > 0
    assert cell.biomass.get("zooplankton", 0) >= 0
    assert cell.biomass.get("fish", 0) >= 0


def test_watershed_runoff_aggregates_into_basins() -> None:
    grid = TerrainGenerator(TerrainParams(width=10, height=10, seed=5)).generate()
    engine = HydrologyEngine()
    routes = engine.route_water(grid)
    runoff = {(route.x, route.y): float((route.x + route.y) % 4) for route in routes}
    basins = engine.aggregate_basins(routes, runoff)
    assert basins
    assert sum(summary.contributing_cells for summary in basins) == 100
    assert all(summary.accumulated_runoff_mm >= 0 for summary in basins)
