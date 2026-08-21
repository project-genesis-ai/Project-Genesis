from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Season(StrEnum):
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"


@dataclass(frozen=True, slots=True)
class SeasonalClimate:
    mean_temperature_c: float
    precipitation_mm: float
    day_length_hours: float

    def __post_init__(self) -> None:
        if self.precipitation_mm < 0 or not 0 <= self.day_length_hours <= 24:
            raise ValueError("invalid seasonal climate")


@dataclass(frozen=True, slots=True)
class SeasonalCycle:
    year_days: float = 365.2422

    def climate(self, day_of_year: float, baseline_temperature_c: float, seasonal_amplitude_c: float, baseline_precipitation_mm: float) -> SeasonalClimate:
        import math
        if not 0 <= day_of_year < self.year_days:
            raise ValueError("day_of_year outside year")
        phase = 2 * math.pi * day_of_year / self.year_days
        temperature = baseline_temperature_c + seasonal_amplitude_c * math.sin(phase - math.pi / 2)
        precipitation = max(0.0, baseline_precipitation_mm * (1.0 + 0.25 * math.sin(phase)))
        day_length = 12.0 + 4.0 * math.sin(phase)
        return SeasonalClimate(temperature, precipitation, day_length)
