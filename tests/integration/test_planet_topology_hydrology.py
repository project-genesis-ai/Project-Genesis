from genesis.planet.groundwater import GroundwaterEngine, GroundwaterState
from genesis.planet.hydrology import HydrologyEngine
from genesis.planet.river_network import RiverNetworkBuilder
from genesis.planet.terrain import TerrainGenerator, TerrainParams
from genesis.planet.topology import TerrainTopologyEngine


def test_terrain_topology_finds_land_and_ocean_regions() -> None:
    grid = TerrainGenerator(TerrainParams(width=20, height=14, seed=19)).generate()
    topology = TerrainTopologyEngine().build(grid)
    assert topology.regions
    assert topology.land_region_count > 0
    assert topology.ocean_region_count > 0


def test_river_network_accumulates_runoff_downstream() -> None:
    grid = TerrainGenerator(TerrainParams(width=12, height=12, seed=2)).generate()
    routes = HydrologyEngine().route_water(grid)
    runoff = {(route.x, route.y): 1.0 for route in routes}
    network = RiverNetworkBuilder().build(routes, runoff)
    assert len(network.segments) == len(routes)
    assert any(segment.discharge_mm > 1.0 for segment in network.segments)


def test_groundwater_recharge_and_discharge_are_bounded() -> None:
    state = GroundwaterState(storage_mm=20, recharge_mm=0, discharge_mm=0, water_table_m=1)
    next_state = GroundwaterEngine().step(state, recharge_mm=10, aquifer_capacity_mm=50, demand_mm=5)
    assert 0 <= next_state.storage_mm <= 50
    assert next_state.discharge_mm >= 0
    assert next_state.water_table_m >= 0
