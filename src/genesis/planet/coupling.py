from __future__ import annotations

from dataclasses import dataclass

from .aquatic import AquaticCell, AquaticSystem
from .atmosphere import AtmosphericState, AtmosphereEngine
from .biomes import BiomeEngine, BiomeState
from .hydrology import HydrologyEngine, HydrologyState, WaterRoute
from .river_network import RiverNetwork, RiverNetworkBuilder
from .terrain import TerrainCell, TerrainGenerator, TerrainParams
from .topology import TerrainTopology, TerrainTopologyEngine


@dataclass(frozen=True, slots=True)
class PlanetCellState:
    terrain: TerrainCell
    atmosphere: AtmosphericState
    hydrology: HydrologyState
    biome: BiomeState


@dataclass(frozen=True, slots=True)
class PlanetSnapshot:
    cells: tuple[tuple[PlanetCellState, ...], ...]
    routes: tuple[WaterRoute, ...]
    aquatic: tuple[tuple[int, int, AquaticCell], ...]
    topology: TerrainTopology
    rivers: RiverNetwork
    tick: int


class PlanetEngine:
    """Coordinates terrain, atmosphere, hydrology, biomes and aquatic ecology."""

    def __init__(self, terrain_params: TerrainParams = TerrainParams()) -> None:
        self.terrain_params = terrain_params
        self.terrain = TerrainGenerator(terrain_params)
        self.atmosphere = AtmosphereEngine()
        self.hydrology = HydrologyEngine()
        self.biomes = BiomeEngine()
        self.aquatic = AquaticSystem()
        self.topology_engine = TerrainTopologyEngine()
        self.river_builder = RiverNetworkBuilder()
        self._terrain_grid: tuple[tuple[TerrainCell, ...], ...] | None = None
        self._topology: TerrainTopology | None = None
        self._routes: tuple[WaterRoute, ...] | None = None
        self._snapshot: PlanetSnapshot | None = None

    @property
    def snapshot(self) -> PlanetSnapshot | None:
        return self._snapshot

    def generate(self, tick: int = 0) -> tuple[tuple[PlanetCellState, ...], ...]:
        return self.step(tick).cells

    def step(self, tick: int) -> PlanetSnapshot:
        if tick < 0:
            raise ValueError("tick cannot be negative")
        if self._terrain_grid is None:
            self._terrain_grid = self.terrain.generate()
            self._topology = self.topology_engine.build(self._terrain_grid)
            self._routes = self.hydrology.route_water(self._terrain_grid)
        snapshot = self._build_snapshot(self._terrain_grid, tick, self._routes or ())
        self._snapshot = snapshot
        return snapshot

    def _build_snapshot(self, terrain: tuple[tuple[TerrainCell, ...], ...], tick: int,
                        routes: tuple[WaterRoute, ...]) -> PlanetSnapshot:
        height = len(terrain)
        width = len(terrain[0]) if height else 0
        total_ocean = sum(1 for row in terrain for cell in row if not cell.land)
        ocean_fraction = total_ocean / max(1, width * height)
        states: list[list[PlanetCellState]] = []
        runoff_by_cell: dict[tuple[int, int], float] = {}
        for y, row in enumerate(terrain):
            state_row: list[PlanetCellState] = []
            latitude = (y / max(1, height - 1) - 0.5) * 180.0
            for cell in row:
                ocean = not cell.land
                atmosphere = self.atmosphere.state(
                    latitude=latitude,
                    elevation_m=cell.elevation_m,
                    tick=tick,
                    moisture=0.82 if ocean else 0.45,
                    ocean_fraction=ocean_fraction,
                )
                hydro = self.hydrology.balance(
                    rainfall_mm=atmosphere.precipitation_mm,
                    temperature_c=atmosphere.temperature_c,
                    humidity=atmosphere.humidity,
                    wind_mps=(atmosphere.wind_u_mps**2 + atmosphere.wind_v_mps**2) ** 0.5,
                    soil_capacity_mm=50.0 if cell.land else 0.0,
                    surface_storage_mm=500.0 if ocean else 0.0,
                )
                runoff_by_cell[(cell.x, cell.y)] = hydro.runoff_mm
                biome = self.biomes.classify(
                    temperature_c=atmosphere.temperature_c,
                    precipitation_mm=atmosphere.precipitation_mm,
                    elevation_m=cell.elevation_m,
                    soil_moisture=min(1.0, hydro.groundwater_mm / 50.0),
                    freshwater=False,
                )
                if ocean and (cell.x, cell.y) not in self.aquatic.cells:
                    self.aquatic.add_cell(
                        cell.x,
                        cell.y,
                        AquaticCell(
                            salinity=1.0,
                            dissolved_oxygen=0.85,
                            nutrients=max(0.2, atmosphere.humidity),
                            depth_m=max(5.0, abs(cell.elevation_m)),
                            temperature_c=max(0.0, atmosphere.temperature_c),
                        ),
                    )
                state_row.append(PlanetCellState(cell, atmosphere, hydro, biome))
            states.append(state_row)
        self.aquatic.step(sunlight=0.65)
        aquatic = tuple(
            (x, y, self.aquatic.cells[(x, y)])
            for y, row in enumerate(terrain)
            for x, cell in enumerate(row)
            if not cell.land
        )
        rivers = self.river_builder.build(routes, runoff_by_cell)
        return PlanetSnapshot(
            tuple(tuple(row) for row in states),
            routes,
            aquatic,
            self._topology or self.topology_engine.build(terrain),
            rivers,
            tick,
        )
