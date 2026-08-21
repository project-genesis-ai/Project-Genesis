from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .terrain import TerrainCell
from .water_cycle import PlanetaryWaterCycle
from .weather_field import WeatherFieldSnapshot


@dataclass(frozen=True, slots=True)
class PlanetaryFeedback:
    """Aggregated climate/hydrology feedback exchanged with the rest of the planet."""

    atmospheric_water_mm: float
    rainfall_mm: float
    evaporation_mm: float
    runoff_mm: float
    groundwater_mm: float
    surface_storage_mm: float
    ocean_fraction: float
    mean_temperature_c: float
    mean_humidity: float
    water_balance_error_mm: float

    def __post_init__(self) -> None:
        values = (
            self.atmospheric_water_mm,
            self.rainfall_mm,
            self.evaporation_mm,
            self.runoff_mm,
            self.groundwater_mm,
            self.surface_storage_mm,
            self.mean_temperature_c,
            self.mean_humidity,
            self.water_balance_error_mm,
        )
        if not all(isfinite(value) for value in values):
            raise ValueError("planetary feedback values must be finite")
        if not 0.0 <= self.ocean_fraction <= 1.0:
            raise ValueError("ocean_fraction must be between 0 and 1")

    @property
    def net_surface_water_change_mm(self) -> float:
        return self.rainfall_mm - self.evaporation_mm - self.runoff_mm


def build_planetary_feedback(
    terrain: tuple[tuple[TerrainCell, ...], ...],
    weather: WeatherFieldSnapshot,
    water: PlanetaryWaterCycle,
) -> PlanetaryFeedback:
    """Build one deterministic planet-scale climate/water feedback vector."""
    total_cells = max(1, len(water.cells))
    ocean_cells = sum(1 for row in terrain for cell in row if not cell.land)
    mean_temperature = sum(cell.climate_temperature_c for cell in water.cells) / total_cells
    mean_humidity = sum(cell.humidity for cell in water.cells) / total_cells
    # Atmospheric water is represented as column-equivalent humidity for the
    # simulation scale. Keeping this quantity explicit prevents future systems
    # from silently treating rainfall as an independent source of water.
    atmospheric_water = sum(cell.humidity * (1.0 + 0.25 * (not terrain[cell.y][cell.x].land)) for cell in water.cells) / total_cells
    return PlanetaryFeedback(
        atmospheric_water_mm=atmospheric_water * 100.0,
        rainfall_mm=water.total_rainfall_mm,
        evaporation_mm=water.total_evaporation_mm,
        runoff_mm=water.total_runoff_mm,
        groundwater_mm=water.total_groundwater_storage_mm,
        surface_storage_mm=water.total_surface_storage_mm,
        ocean_fraction=ocean_cells / max(1, len(terrain) * len(terrain[0]) if terrain else 1),
        mean_temperature_c=mean_temperature,
        mean_humidity=mean_humidity,
        water_balance_error_mm=water.max_balance_error_mm,
    )
