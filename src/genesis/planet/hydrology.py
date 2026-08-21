from __future__ import annotations

from dataclasses import dataclass

from .terrain import TerrainCell


@dataclass(frozen=True, slots=True)
class HydrologyState:
    rainfall_mm: float
    runoff_mm: float
    infiltration_mm: float
    groundwater_mm: float
    river_flow: float
    lake_storage: float
    evaporation_mm: float

    def __post_init__(self) -> None:
        for value in (self.rainfall_mm, self.runoff_mm, self.infiltration_mm, self.groundwater_mm,
                      self.river_flow, self.lake_storage, self.evaporation_mm):
            if value < 0:
                raise ValueError("hydrology values cannot be negative")


class HydrologyEngine:
    """Cell-scale water balance and downhill runoff routing."""

    def __init__(self, infiltration_rate: float = 0.3, groundwater_recharge_rate: float = 0.25) -> None:
        if not 0 <= infiltration_rate <= 1 or not 0 <= groundwater_recharge_rate <= 1:
            raise ValueError("rates must be between 0 and 1")
        self.infiltration_rate = infiltration_rate
        self.groundwater_recharge_rate = groundwater_recharge_rate

    @staticmethod
    def evaporation(temperature_c: float, humidity: float, wind_mps: float) -> float:
        if not 0 <= humidity <= 1 or wind_mps < 0:
            raise ValueError("invalid atmospheric inputs")
        return max(0.0, (0.12 * max(0.0, temperature_c + 5.0)) * (1.0 - humidity) * (1.0 + 0.03 * wind_mps))

    def balance(self, *, rainfall_mm: float, temperature_c: float, humidity: float, wind_mps: float,
                soil_capacity_mm: float, surface_storage_mm: float) -> HydrologyState:
        if rainfall_mm < 0 or soil_capacity_mm < 0 or surface_storage_mm < 0:
            raise ValueError("water quantities cannot be negative")
        evaporation = min(surface_storage_mm + rainfall_mm, self.evaporation(temperature_c, humidity, wind_mps))
        available = max(0.0, rainfall_mm - evaporation)
        infiltration = min(available * self.infiltration_rate, soil_capacity_mm)
        recharge = infiltration * self.groundwater_recharge_rate
        runoff = max(0.0, available - infiltration)
        river_flow = runoff
        groundwater = recharge
        lake = max(0.0, surface_storage_mm + runoff + infiltration - evaporation - recharge)
        return HydrologyState(rainfall_mm, runoff, infiltration, groundwater, river_flow, lake, evaporation)

    @staticmethod
    def downhill_neighbor(grid: tuple[tuple[TerrainCell, ...], ...], x: int, y: int) -> tuple[int, int] | None:
        height = len(grid)
        width = len(grid[0]) if height else 0
        if not (0 <= x < width and 0 <= y < height):
            raise IndexError("cell coordinates out of bounds")
        current = grid[y][x].elevation_m
        candidates: list[tuple[float, int, int]] = []
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < width and 0 <= ny < height:
                delta = grid[ny][nx].elevation_m - current
                if delta < 0:
                    candidates.append((grid[ny][nx].elevation_m, nx, ny))
        if not candidates:
            return None
        _, nx, ny = min(candidates)
        return nx, ny
