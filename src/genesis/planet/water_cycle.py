from __future__ import annotations

from dataclasses import dataclass

from .groundwater import GroundwaterEngine, GroundwaterState
from .hydrology import BasinSummary, HydrologyEngine, HydrologyState
from .terrain import TerrainCell
from .weather_field import RegionalWeatherEngine, WeatherFieldSnapshot


@dataclass(frozen=True, slots=True)
class PlanetaryWaterCell:
    """Authoritative water/climate state produced for one terrain cell."""

    x: int
    y: int
    latitude: float
    climate_temperature_c: float
    humidity: float
    rainfall_mm: float
    surface_storage_mm: float
    hydrology: HydrologyState
    groundwater: GroundwaterState

    @property
    def water_balance_residual_mm(self) -> float:
        h = self.hydrology
        return (h.rainfall_mm + self.surface_storage_mm) - (
            h.evaporation_mm + h.infiltration_mm + h.runoff_mm
        )


@dataclass(frozen=True, slots=True)
class PlanetaryWaterCycle:
    """Deterministic coupling of terrain, regional weather, surface water and aquifers."""

    cells: tuple[PlanetaryWaterCell, ...]
    basins: tuple[BasinSummary, ...]

    @property
    def total_rainfall_mm(self) -> float:
        return sum(cell.hydrology.rainfall_mm for cell in self.cells)

    @property
    def total_runoff_mm(self) -> float:
        return sum(cell.hydrology.runoff_mm for cell in self.cells)

    @property
    def total_groundwater_storage_mm(self) -> float:
        return sum(cell.groundwater.storage_mm for cell in self.cells)

    @property
    def total_surface_storage_mm(self) -> float:
        return sum(cell.surface_storage_mm for cell in self.cells)

    @property
    def total_evaporation_mm(self) -> float:
        return sum(cell.hydrology.evaporation_mm for cell in self.cells)

    @property
    def max_balance_error_mm(self) -> float:
        return max((abs(cell.water_balance_residual_mm) for cell in self.cells), default=0.0)


class PlanetaryWaterCycleEngine:
    """Run one coupled atmosphere-to-groundwater tick over a terrain grid.

    Closed depressions retain their routed runoff as surface water for the next
    tick. This makes lake storage persistent instead of recreating it from zero
    every simulation step while preserving deterministic water accounting.
    """

    def __init__(
        self,
        *,
        hydrology: HydrologyEngine | None = None,
        groundwater: GroundwaterEngine | None = None,
        weather: RegionalWeatherEngine | None = None,
    ) -> None:
        self.hydrology = hydrology or HydrologyEngine()
        self.groundwater = groundwater or GroundwaterEngine()
        self.weather = weather or RegionalWeatherEngine()
        self._surface_storage: dict[tuple[int, int], float] = {}

    @staticmethod
    def _latitude(y: int, height: int) -> float:
        if height < 2:
            return 0.0
        return 90.0 - (180.0 * y / (height - 1))

    def _surface_storage_for_cell(
        self,
        key: tuple[int, int],
        supplied: dict[tuple[int, int], float],
    ) -> float:
        if key in self._surface_storage:
            return self._surface_storage[key]
        value = supplied.get(key, 0.0)
        if value < 0.0:
            raise ValueError("surface storage cannot be negative")
        return value

    def run(
        self,
        grid: tuple[tuple[TerrainCell, ...], ...],
        *,
        tick: int,
        moisture_by_cell: dict[tuple[int, int], float] | None = None,
        surface_storage_by_cell: dict[tuple[int, int], float] | None = None,
        groundwater_by_cell: dict[tuple[int, int], GroundwaterState] | None = None,
        water_demand_by_cell: dict[tuple[int, int], float] | None = None,
        weather_snapshot: WeatherFieldSnapshot | None = None,
        aquifer_capacity_mm: float = 1000.0,
        soil_capacity_mm: float = 100.0,
    ) -> PlanetaryWaterCycle:
        if tick < 0:
            raise ValueError("tick cannot be negative")
        if not grid or not grid[0]:
            return PlanetaryWaterCycle((), ())
        width = len(grid[0])
        if any(len(row) != width for row in grid):
            raise ValueError("terrain grid must be rectangular")
        if aquifer_capacity_mm < 0 or soil_capacity_mm < 0:
            raise ValueError("water capacities cannot be negative")

        moisture_by_cell = moisture_by_cell or {}
        surface_storage_by_cell = surface_storage_by_cell or {}
        groundwater_by_cell = groundwater_by_cell or {}
        water_demand_by_cell = water_demand_by_cell or {}
        height = len(grid)
        elevation = {(cell.x, cell.y): cell.elevation_m for row in grid for cell in row}
        moisture: dict[tuple[int, int], float] = {}
        for row in grid:
            for cell in row:
                value = moisture_by_cell.get((cell.x, cell.y), 0.5)
                if not 0.0 <= value <= 1.0:
                    raise ValueError("cell moisture must be between 0 and 1")
                demand = water_demand_by_cell.get((cell.x, cell.y), 0.0)
                if demand < 0:
                    raise ValueError("cell water demand cannot be negative")
                moisture[(cell.x, cell.y)] = value
        if weather_snapshot is None:
            land_count = sum(1 for row in grid for cell in row if cell.land)
            ocean_fraction = 1.0 - land_count / (width * height)
            weather_snapshot = self.weather.step(
                width=width,
                height=height,
                tick=tick,
                latitude_for_row=lambda y: self._latitude(y, height),
                elevation=elevation,
                moisture=moisture,
                ocean_fraction=ocean_fraction,
            )
        if weather_snapshot.width != width or weather_snapshot.height != height or weather_snapshot.tick != tick:
            raise ValueError("weather snapshot does not match terrain dimensions or tick")
        weather_by_cell = {(cell.x, cell.y): cell.state for cell in weather_snapshot.cells}
        if len(weather_by_cell) != width * height:
            raise ValueError("weather snapshot must contain every terrain cell")

        routes = self.hydrology.route_water(grid)
        terminal_by_cell = {(route.x, route.y): route.terminal for route in routes}
        cells: list[PlanetaryWaterCell] = []
        runoff_by_cell: dict[tuple[int, int], float] = {}
        next_surface_storage: dict[tuple[int, int], float] = {}
        for row in grid:
            for terrain in row:
                key = (terrain.x, terrain.y)
                climate = weather_by_cell[key]
                previous_groundwater = groundwater_by_cell.get(key, GroundwaterState())
                surface_storage = self._surface_storage_for_cell(key, surface_storage_by_cell)
                demand = water_demand_by_cell.get(key, 0.0)
                wind = (climate.wind_u_mps**2 + climate.wind_v_mps**2) ** 0.5
                balance = self.hydrology.balance(
                    rainfall_mm=climate.precipitation_mm,
                    temperature_c=climate.temperature_c,
                    humidity=climate.humidity,
                    wind_mps=wind,
                    soil_capacity_mm=soil_capacity_mm if terrain.land else 0.0,
                    surface_storage_mm=surface_storage,
                )
                groundwater = self.groundwater.step(
                    previous_groundwater,
                    recharge_mm=balance.groundwater_mm,
                    aquifer_capacity_mm=aquifer_capacity_mm if terrain.land else 0.0,
                    demand_mm=demand,
                )
                retained = balance.lake_storage if terminal_by_cell.get(key) in {"lake_or_watershed", "closed_depression"} else 0.0
                next_surface_storage[key] = max(0.0, retained)
                cells.append(
                    PlanetaryWaterCell(
                        terrain.x,
                        terrain.y,
                        self._latitude(terrain.y, height),
                        climate.temperature_c,
                        climate.humidity,
                        climate.precipitation_mm,
                        surface_storage,
                        balance,
                        groundwater,
                    )
                )
                runoff_by_cell[key] = balance.runoff_mm

        self._surface_storage = next_surface_storage
        basins = self.hydrology.aggregate_basins(routes, runoff_by_cell)
        return PlanetaryWaterCycle(tuple(cells), basins)
