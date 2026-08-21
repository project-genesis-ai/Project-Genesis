from __future__ import annotations

from dataclasses import dataclass

from genesis.world.environment import Biome, EnvironmentCell


@dataclass(slots=True)
class ForestDynamics:
    """Simple biomass dynamics driven by water, temperature, and vegetation."""

    growth_rate_per_tick: float = 0.002
    base_water_need_mm: float = 0.5
    temperature_optimum_c: float = 24.0

    def step(self, cell: EnvironmentCell, ticks: int = 1) -> None:
        if cell.biome != Biome.FOREST:
            return
        if ticks < 0:
            raise ValueError("ticks cannot be negative")
        water_factor = min(1.0, cell.water_mm / max(self.base_water_need_mm, 1e-9))
        temperature_factor = max(0.0, 1.0 - abs(cell.temperature_c - self.temperature_optimum_c) / 40.0)
        growth = self.growth_rate_per_tick * water_factor * temperature_factor * ticks
        cell.vegetation = min(1.0, cell.vegetation + growth)
        cell.water_mm = max(0.0, cell.water_mm - self.base_water_need_mm * 0.1 * ticks)
