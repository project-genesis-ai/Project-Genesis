from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class ClimateState:
    """Local climate variables at one simulation tick."""

    temperature_c: float
    humidity: float
    precipitation_mm: float
    wind_mps: float

    def __post_init__(self) -> None:
        if not 0 <= self.humidity <= 1:
            raise ValueError("humidity must be between 0 and 1")
        if self.precipitation_mm < 0 or self.wind_mps < 0:
            raise ValueError("precipitation and wind cannot be negative")


class ClimateEngine:
    """Cheap deterministic local weather model; parameters remain replaceable."""

    def state(self, *, latitude: float, elevation_m: float, tick: int, moisture: float = 0.5) -> ClimateState:
        if not -90 <= latitude <= 90:
            raise ValueError("latitude must be between -90 and 90")
        if tick < 0:
            raise ValueError("tick cannot be negative")
        if moisture < 0:
            raise ValueError("moisture cannot be negative")
        seasonal = math.sin((tick % 365) * 2.0 * math.pi / 365.0)
        lat_factor = 1.0 - abs(latitude) / 90.0
        temperature = 30.0 * lat_factor - max(elevation_m, 0.0) * 0.0065 + 8.0 * seasonal * lat_factor
        humidity = min(1.0, max(0.0, moisture * (0.75 + 0.2 * math.cos(seasonal))))
        precipitation = max(0.0, humidity * (4.0 + 3.0 * max(0.0, seasonal)))
        wind = 2.0 + abs(math.sin(tick * 0.17 + latitude)) * 8.0
        return ClimateState(temperature, humidity, precipitation, wind)
