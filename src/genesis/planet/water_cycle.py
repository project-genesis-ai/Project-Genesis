from __future__ import annotations

from dataclasses import dataclass

from .groundwater import GroundwaterEngine, GroundwaterState
from .hydrology import BasinSummary, HydrologyEngine, HydrologyState
from .terrain import TerrainCell
from .weather_field import RegionalWeatherEngine


@dataclass(frozen=True, slots=True)
class PlanetaryWaterCell:
    """Authoritative water/climate state produced for one terrain cell."""

    x: int
    y: int
    latitude: float
    climate_temperature_c: float
    humidity: float
    rainfall_mm: float
    hydrology: HydrologyState
    groundwater: GroundwaterState

    @property
    def water_balance_residual_mm(self) -> float:
        h = self.hydrology
        return h.rainfall_mm + (h.runoff_mm * 0.0) - (h.evaporation_mm + h.infiltration_mm + h.runoff_mm)


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
    def max_balance_error_mm(self) -> float:
        return max((abs(cell.water_balance_residual_mm) for cell in self.cells), default=0.0)


class PlanetaryWaterCycleEngine:
    """Run one coupled atmosphere-to-groundwater tick over a terrain grid."""

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

    @staticmethod
    def _latitude(y: int, height: int) -> float:
        if height < 2:
            return 0.0
        return 90.0 - (180.0 * y / (height - 1))

    def run(
        self,
        grid: tuple[tuple[TerrainCell, ...], ...],
        *,
        tick: int,
        moisture_by_cell: dict[tuple[int, int], float] | None = None,
        surface_storage_by_cell: dict[tuple[int, int], float] | None = None,
        groundwater_by_cell: dict[tuple[int, int], GroundwaterState] | None = None,
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
        height = len(grid)
        elevation = {(cell.x, cell.y): cell.elevation_m for row in grid for cell in row}
        moisture: dict[tuple[int, int], float] = {}
        for row in grid:
            for cell in row:
                value = moisture_by_cell.get((cell.x, cell.y), 0.5)
                if not 0.0 <= value <= 1.0:
                    raise ValueError("cell moisture must be between 0 and 1")
                moisture[(cell.x, cell.y)] = value
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
        weather_by_cell = {(cell.x, cell.y): cell.state for cell in weather_snapshot.cells}

        cells: list[PlanetaryWaterCell] = []
        runoff_by_cell: dict[tuple[int, int], float] = {}
        for row in grid:
            for terrain in row:
                key = (terrain.x, terrain.y)
                climate = weather_by_cell[key]
                previous_groundwater = groundwater_by_cell.get(key, GroundwaterState())
                wind = (climate.wind_u_mps**2 + climate.wind_v_mps**2) ** 0.5
                balance = self.hydrology.balance(
                    rainfall_mm=climate.precipitation_mm,
                    temperature_c=climate.temperature_c,
                    humidity=climate.humidity,
                    wind_mps=wind,
                    soil_capacity_mm=soil_capacity_mm if terrain.land else 0.0,
                    surface_storage_mm=surface_storage_by_cell.get(key, 0.0),
                )
                groundwater = self.groundwater.step(
                    previous_groundwater,
                    recharge_mm=balance.groundwater_mm,
                    aquifer_capacity_mm=aquifer_capacity_mm if terrain.land else 0.0,
                )
                cells.append(
                    PlanetaryWaterCell(
                        terrain.x,
                        terrain.y,
                        self._latitude(terrain.y, height),
                        climate.temperature_c,
                        climate.humidity,
                        climate.precipitation_mm,
                        balance,
                        groundwater,
                    )
                )
                runoff_by_cell[key] = balance.runoff_mm

        routes = self.hydrology.route_water(grid)
        basins = self.hydrology.aggregate_basins(routes, runoff_by_cell)
        return PlanetaryWaterCycle(tuple(cells), basins)
