from __future__ import annotations

from dataclasses import dataclass
import math

from .atmosphere import AtmosphericState, AtmosphereEngine


@dataclass(frozen=True, slots=True)
class WeatherCell:
    x: int
    y: int
    state: AtmosphericState


@dataclass(frozen=True, slots=True)
class WeatherFieldSnapshot:
    width: int
    height: int
    cells: tuple[WeatherCell, ...]
    tick: int


class RegionalWeatherEngine:
    """Spatially coupled weather field with lightweight moisture/wind advection."""

    def __init__(self, atmosphere: AtmosphereEngine | None = None) -> None:
        self.atmosphere = atmosphere or AtmosphereEngine()

    @staticmethod
    def _neighbor_mean(values: dict[tuple[int, int], float], x: int, y: int) -> float:
        samples: list[float] = []
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            value = values.get((nx, ny))
            if value is not None:
                samples.append(value)
        return sum(samples) / len(samples) if samples else values.get((x, y), 0.0)

    def step(
        self,
        *,
        width: int,
        height: int,
        tick: int,
        latitude_for_row: callable,
        elevation: dict[tuple[int, int], float],
        moisture: dict[tuple[int, int], float],
        ocean_fraction: float,
    ) -> WeatherFieldSnapshot:
        if width <= 0 or height <= 0 or tick < 0:
            raise ValueError("invalid weather field dimensions or tick")
        base: dict[tuple[int, int], AtmosphericState] = {}
        for y in range(height):
            latitude = float(latitude_for_row(y))
            for x in range(width):
                key = (x, y)
                base[key] = self.atmosphere.state(
                    latitude=latitude,
                    elevation_m=elevation.get(key, 0.0),
                    tick=tick,
                    moisture=max(0.0, min(1.0, moisture.get(key, 0.5))),
                    ocean_fraction=ocean_fraction,
                )

        humidity: dict[tuple[int, int], float] = {key: state.humidity for key, state in base.items()}
        wind_u: dict[tuple[int, int], float] = {key: state.wind_u_mps for key, state in base.items()}
        wind_v: dict[tuple[int, int], float] = {key: state.wind_v_mps for key, state in base.items()}
        cells: list[WeatherCell] = []
        for y in range(height):
            for x in range(width):
                key = (x, y)
                state = base[key]
                neighbor_humidity = self._neighbor_mean(humidity, x, y)
                neighbor_u = self._neighbor_mean(wind_u, x, y)
                neighbor_v = self._neighbor_mean(wind_v, x, y)
                coupled_humidity = max(0.0, min(1.0, 0.78 * state.humidity + 0.22 * neighbor_humidity))
                coupled_u = 0.85 * state.wind_u_mps + 0.15 * neighbor_u
                coupled_v = 0.85 * state.wind_v_mps + 0.15 * neighbor_v
                convergence = abs(coupled_u - neighbor_u) + abs(coupled_v - neighbor_v)
                cloud = max(0.0, min(1.0, 0.7 * state.cloud_cover + 0.3 * coupled_humidity))
                storm = max(0.0, min(1.0, state.storm_intensity + convergence * 0.015 + (coupled_humidity - 0.7) * 0.2))
                precipitation = max(0.0, state.precipitation_mm * (0.75 + 0.25 * cloud) * (1.0 + 0.6 * storm))
                cells.append(WeatherCell(
                    x,
                    y,
                    AtmosphericState(state.temperature_c, state.pressure_kpa, coupled_humidity,
                                     coupled_u, coupled_v, cloud, precipitation, storm),
                ))
        return WeatherFieldSnapshot(width, height, tuple(cells), tick)
