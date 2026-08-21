from __future__ import annotations

from dataclasses import dataclass, replace

from .aquatic import AquaticCell, AquaticSystem
from .atmosphere import AtmosphericState, AtmosphereEngine
from .biomes import BiomeEngine, BiomeState
from .hydrology import HydrologyEngine, HydrologyState, WaterRoute
from .hydrology_runtime import HydrologyRuntime
from .ocean_depth import OceanEcosystem
from .river_network import RiverNetwork, RiverNetworkBuilder
from .terrain import TerrainCell, TerrainGenerator, TerrainParams
from .topology import TerrainTopology, TerrainTopologyEngine
from .weather_field import RegionalWeatherEngine


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
    deep_ocean: tuple[tuple[int, int, OceanEcosystem], ...] = ()


class PlanetEngine:
    """Coordinates terrain, regional weather, hydrology, biomes and aquatic ecology."""

    def __init__(self, terrain_params: TerrainParams = TerrainParams()) -> None:
        self.terrain_params = terrain_params
        self.terrain = TerrainGenerator(terrain_params)
        self.atmosphere = AtmosphereEngine()
        self.regional_weather = RegionalWeatherEngine(self.atmosphere)
        self.hydrology = HydrologyEngine()
        self.hydrology_runtime = HydrologyRuntime()
        self.biomes = BiomeEngine()
        self.aquatic = AquaticSystem()
        self.ocean_ecosystems: dict[tuple[int, int], OceanEcosystem] = {}
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

    def _build_snapshot(
        self,
        terrain: tuple[tuple[TerrainCell, ...], ...],
        tick: int,
        routes: tuple[WaterRoute, ...],
    ) -> PlanetSnapshot:
        height = len(terrain)
        width = len(terrain[0]) if height else 0
        total_ocean = sum(1 for row in terrain for cell in row if not cell.land)
        ocean_fraction = total_ocean / max(1, width * height)
        latitude_for_row = lambda y: (y / max(1, height - 1) - 0.5) * 180.0
        elevation = {(cell.x, cell.y): cell.elevation_m for row in terrain for cell in row}
        moisture = {
            (cell.x, cell.y): 0.82 if not cell.land else 0.45
            for row in terrain
            for cell in row
        }
        weather = self.regional_weather.step(
            width=width,
            height=height,
            tick=tick,
            latitude_for_row=latitude_for_row,
            elevation=elevation,
            moisture=moisture,
            ocean_fraction=ocean_fraction,
        )
        weather_by_cell = {(cell.x, cell.y): cell.state for cell in weather.cells}

        states: list[list[PlanetCellState]] = []
        runoff_by_cell: dict[tuple[int, int], float] = {}
        for row in terrain:
            state_row: list[PlanetCellState] = []
            for cell in row:
                ocean = not cell.land
                atmosphere = weather_by_cell[(cell.x, cell.y)]
                hydro = self.hydrology.balance(
                    rainfall_mm=atmosphere.precipitation_mm,
                    temperature_c=atmosphere.temperature_c,
                    humidity=atmosphere.humidity,
                    wind_mps=(atmosphere.wind_u_mps**2 + atmosphere.wind_v_mps**2) ** 0.5,
                    soil_capacity_mm=50.0 if cell.land else 0.0,
                    surface_storage_mm=500.0 if ocean else 0.0,
                )
                water_runtime = self.hydrology_runtime.step_cell((cell.x, cell.y), state=hydro)
                hydro = replace(hydro, groundwater_mm=water_runtime.groundwater.storage_mm)
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
        deep_ocean: list[tuple[int, int, OceanEcosystem]] = []
        for row in terrain:
            for cell in row:
                if cell.land:
                    continue
                depth_m = abs(cell.elevation_m)
                if depth_m <= 1000.0:
                    continue
                key = (cell.x, cell.y)
                aquatic_cell = self.aquatic.cells[key]
                ecosystem = self.ocean_ecosystems.get(key)
                if ecosystem is None:
                    ecosystem = OceanEcosystem.create(
                        surface_temperature_c=weather_by_cell[key].temperature_c,
                        depth_m=depth_m,
                        nutrients=aquatic_cell.nutrients,
                    )
                    self.ocean_ecosystems[key] = ecosystem
                photic = ecosystem.layers["photic"]
                photic.temperature_c = weather_by_cell[key].temperature_c
                photic.nutrients = max(photic.nutrients, aquatic_cell.nutrients)
                ecosystem.step()
                aquatic_cell.nutrients = max(0.0, photic.nutrients)
                aquatic_cell.dissolved_oxygen = min(1.0, max(aquatic_cell.dissolved_oxygen, photic.oxygen))
                aquatic_cell.biomass["ocean_phytoplankton"] = photic.biomass.get("phytoplankton", 0.0)
                deep_ocean.append((cell.x, cell.y, ecosystem))

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
            tuple(deep_ocean),
        )
