from __future__ import annotations

from dataclasses import dataclass, replace

from .aquatic import AquaticCell, AquaticSystem
from .atmosphere import AtmosphericState, AtmosphereEngine
from .biomes import BiomeEngine, BiomeState
from .civilization_feedback import EnvironmentalImpact
from .hydrology import HydrologyEngine, HydrologyState, WaterRoute
from .hydrology_runtime import HydrologyRuntime
from .ocean_depth import OceanEcosystem
from .river_network import RiverNetwork, RiverNetworkBuilder
from .terrain import TerrainCell, TerrainGenerator, TerrainParams
from .topology import TerrainTopology, TerrainTopologyEngine
from .water_cycle import PlanetaryWaterCycleEngine
from .weather_field import RegionalWeatherEngine


@dataclass(frozen=True, slots=True)
class PlanetCellState:
    terrain: TerrainCell
    atmosphere: AtmosphericState
    hydrology: HydrologyState
    biome: BiomeState
    surface_water_quality: float = 1.0
    pollution: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.surface_water_quality <= 1.0 or self.pollution < 0.0:
            raise ValueError("invalid planetary water quality state")


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
    """Coordinates terrain, weather, authoritative water, ecology and civilization feedback."""

    def __init__(self, terrain_params: TerrainParams = TerrainParams()) -> None:
        self.terrain_params = terrain_params
        self.terrain = TerrainGenerator(terrain_params)
        self.atmosphere = AtmosphereEngine()
        self.regional_weather = RegionalWeatherEngine(self.atmosphere)
        self.hydrology = HydrologyEngine()
        self.hydrology_runtime = HydrologyRuntime()
        self.water_cycle = PlanetaryWaterCycleEngine(
            hydrology=self.hydrology,
            groundwater=self.hydrology_runtime.groundwater_engine,
            weather=self.regional_weather,
        )
        self.biomes = BiomeEngine()
        self.aquatic = AquaticSystem()
        self.ocean_ecosystems: dict[tuple[int, int], OceanEcosystem] = {}
        self.civilization_impacts: dict[tuple[int, int], EnvironmentalImpact] = {}
        self.topology_engine = TerrainTopologyEngine()
        self.river_builder = RiverNetworkBuilder()
        self._terrain_grid: tuple[tuple[TerrainCell, ...], ...] | None = None
        self._topology: TerrainTopology | None = None
        self._routes: tuple[WaterRoute, ...] | None = None
        self._snapshot: PlanetSnapshot | None = None

    @property
    def snapshot(self) -> PlanetSnapshot | None:
        return self._snapshot

    def set_civilization_impacts(
        self,
        impacts: dict[tuple[int, int], EnvironmentalImpact],
    ) -> None:
        """Replace the authoritative cell-level civilization pressure field."""
        for key, impact in impacts.items():
            if len(key) != 2:
                raise ValueError("civilization impact key must contain x and y")
            if not isinstance(impact, EnvironmentalImpact):
                raise TypeError("civilization impacts must contain EnvironmentalImpact values")
        self.civilization_impacts = dict(impacts)

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

    def _previous_moisture(
        self,
        terrain: tuple[tuple[TerrainCell, ...], ...],
    ) -> dict[tuple[int, int], float]:
        moisture: dict[tuple[int, int], float] = {}
        previous = self._snapshot
        if previous is None:
            for row in terrain:
                for cell in row:
                    moisture[(cell.x, cell.y)] = 0.82 if not cell.land else 0.45
            return moisture

        for row in terrain:
            for cell in row:
                key = (cell.x, cell.y)
                previous_cell = previous.cells[cell.y][cell.x]
                groundwater = max(0.0, min(1.0, previous_cell.hydrology.groundwater_mm / 100.0))
                quality = previous_cell.surface_water_quality
                if cell.land:
                    moisture[key] = max(0.15, min(0.95, 0.20 + 0.70 * groundwater + 0.10 * quality))
                else:
                    moisture[key] = max(0.35, min(1.0, 0.70 + 0.30 * quality))
        return moisture

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
        moisture = self._previous_moisture(terrain)
        weather = self.regional_weather.step(
            width=width,
            height=height,
            tick=tick,
            latitude_for_row=latitude_for_row,
            elevation=elevation,
            moisture=moisture,
            ocean_fraction=ocean_fraction,
        )
        demand_by_cell = {
            key: max(0.0, impact.water_extraction)
            for key, impact in self.civilization_impacts.items()
        }
        surface_storage = {
            (cell.x, cell.y): 500.0 if not cell.land else 0.0
            for row in terrain
            for cell in row
        }
        water_cycle = self.water_cycle.run(
            terrain,
            tick=tick,
            moisture_by_cell=moisture,
            surface_storage_by_cell=surface_storage,
            groundwater_by_cell=dict(self.hydrology_runtime.groundwater),
            water_demand_by_cell=demand_by_cell,
            weather_snapshot=weather,
            aquifer_capacity_mm=250.0,
            soil_capacity_mm=50.0,
        )
        water_by_cell = {(cell.x, cell.y): cell for cell in water_cycle.cells}
        weather_by_cell = {(cell.x, cell.y): cell.state for cell in weather.cells}

        states: list[list[PlanetCellState]] = []
        runoff_by_cell: dict[tuple[int, int], float] = {}
        for row in terrain:
            state_row: list[PlanetCellState] = []
            for cell in row:
                key = (cell.x, cell.y)
                impact = self.civilization_impacts.get(key)
                ocean = not cell.land
                water_cell = water_by_cell[key]
                water_runtime = self.hydrology_runtime.commit_cell(
                    key,
                    state=water_cell.hydrology,
                    groundwater=water_cell.groundwater,
                    civilization=impact,
                )
                hydro = replace(
                    water_cell.hydrology,
                    groundwater_mm=water_runtime.groundwater.storage_mm,
                )
                atmosphere = weather_by_cell[key]
                runoff_by_cell[key] = hydro.runoff_mm
                soil_moisture = min(1.0, hydro.groundwater_mm / 50.0)
                if impact is not None:
                    soil_moisture *= max(0.0, 1.0 - min(1.0, impact.land_conversion) * 0.35)
                biome = self.biomes.classify(
                    temperature_c=atmosphere.temperature_c,
                    precipitation_mm=atmosphere.precipitation_mm,
                    elevation_m=cell.elevation_m,
                    soil_moisture=soil_moisture,
                    freshwater=False,
                )
                if ocean and key not in self.aquatic.cells:
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
                state_row.append(
                    PlanetCellState(
                        cell,
                        atmosphere,
                        hydro,
                        biome,
                        water_runtime.surface_water_quality,
                        water_runtime.pollution,
                    )
                )
            states.append(state_row)

        self.aquatic.step(sunlight=0.65)
        deep_ocean: list[tuple[int, int, OceanEcosystem]] = []
        for row in terrain:
            for cell in row:
                if cell.land:
                    continue
                key = (cell.x, cell.y)
                depth_m = abs(cell.elevation_m)
                if depth_m <= 1000.0:
                    continue
                aquatic_cell = self.aquatic.cells[key]
                impact = self.civilization_impacts.get(key)
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
                pollution = 0.0 if impact is None else min(1.0, impact.pollution)
                extraction = 0.0 if impact is None else max(0.0, impact.water_extraction)
                aquatic_cell.nutrients = max(0.0, photic.nutrients * (1.0 - pollution * 0.5))
                aquatic_cell.dissolved_oxygen = min(
                    1.0,
                    max(0.0, photic.oxygen * (1.0 - pollution * 0.7) - extraction * 0.02),
                )
                aquatic_cell.biomass["ocean_phytoplankton"] = photic.biomass.get("phytoplankton", 0.0) * (1.0 - pollution * 0.6)
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
