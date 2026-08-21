from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class AtmosphericState:
    temperature_c: float
    pressure_kpa: float
    humidity: float
    wind_u_mps: float
    wind_v_mps: float
    cloud_cover: float
    precipitation_mm: float
    storm_intensity: float

    def __post_init__(self) -> None:
        if not 0 <= self.humidity <= 1:
            raise ValueError("humidity must be between 0 and 1")
        if not 0 <= self.cloud_cover <= 1 or self.precipitation_mm < 0 or self.storm_intensity < 0:
            raise ValueError("invalid atmospheric state")


class AtmosphereEngine:
    """Deterministic regional weather model driven by latitude, elevation and moisture."""

    def state(self, *, latitude: float, elevation_m: float, tick: int, moisture: float = 0.5,
              ocean_fraction: float = 0.62) -> AtmosphericState:
        if not -90 <= latitude <= 90:
            raise ValueError("latitude must be between -90 and 90")
        if tick < 0 or elevation_m < -12000:
            raise ValueError("invalid time or elevation")
        if not 0 <= moisture <= 1:
            raise ValueError("moisture must be between 0 and 1")
        if not 0 <= ocean_fraction <= 1:
            raise ValueError("ocean_fraction must be between 0 and 1")

        day_angle = 2.0 * math.pi * (tick % 365) / 365.0
        latitude_factor = max(0.0, 1.0 - abs(latitude) / 90.0)
        seasonal = math.sin(day_angle) * math.cos(math.radians(latitude))
        diurnal = math.sin(2.0 * math.pi * ((tick % 1_0_000) / 1_000.0))
        base_temp = 31.0 * latitude_factor - max(0.0, elevation_m) * 0.0065
        temperature = base_temp + 9.0 * seasonal + 1.5 * diurnal

        pressure = 101.325 * math.exp(-max(0.0, elevation_m) / 8434.5)
        humidity = min(1.0, max(0.0, moisture * (0.62 + 0.28 * ocean_fraction) + 0.08 * math.cos(day_angle)))
        cloud_cover = min(1.0, max(0.0, humidity * 0.92 + max(0.0, seasonal) * 0.15))
        precipitation = max(0.0, cloud_cover * humidity * (1.4 + 4.0 * ocean_fraction + max(0.0, -temperature) * 0.015))

        coriolis = math.sin(math.radians(latitude))
        u = 5.0 * math.cos(day_angle + latitude * 0.03) + 2.0 * coriolis
        v = 3.0 * math.sin(day_angle * 0.7 + latitude * 0.02) + 1.5 * math.cos(latitude * 0.05)
        convergence = abs(u) + abs(v)
        storm = max(0.0, min(1.0, (humidity - 0.72) * 2.5 + (convergence - 5.0) * 0.03))
        precipitation *= 1.0 + storm * 2.0
        return AtmosphericState(temperature, pressure, humidity, u, v, cloud_cover, precipitation, storm)
