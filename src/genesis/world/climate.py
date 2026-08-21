from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin


@dataclass(slots=True)
class ClimateCell:
    """Continuous climate state for one spatial region."""

    temperature_c: float = 20.0
    humidity: float = 0.5
    precipitation_mm: float = 0.0
    wind_mps: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.humidity <= 1.0:
            raise ValueError("humidity must be between 0 and 1")
        if self.precipitation_mm < 0.0 or self.wind_mps < 0.0:
            raise ValueError("precipitation and wind cannot be negative")


@dataclass(slots=True)
class ClimateModel:
    """Low-cost seasonal climate model; deterministic and suitable for ABM coupling."""

    seasonal_amplitude_c: float = 12.0
    base_temperature_c: float = 20.0
    moisture_response: float = 0.1

    def step(self, cell: ClimateCell, tick: int, ticks_per_year: int = 365) -> None:
        if tick < 0 or ticks_per_year <= 0:
            raise ValueError("tick must be non-negative and ticks_per_year positive")
        phase = 2.0 * pi * (tick % ticks_per_year) / ticks_per_year
        cell.temperature_c = self.base_temperature_c + self.seasonal_amplitude_c * sin(phase)
        seasonal_moisture = 0.5 + 0.5 * cos(phase)
        cell.humidity = max(0.0, min(1.0, cell.humidity + (seasonal_moisture - cell.humidity) * self.moisture_response))
        cell.precipitation_mm = max(0.0, (cell.humidity - 0.45) * 20.0)
        cell.wind_mps = max(0.0, 3.0 + 2.0 * sin(phase * 2.0))
