from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class Physiology:
    """Dimensionally explicit baseline physiology for terrestrial organisms.

    The model uses allometric metabolic scaling: basal metabolic demand scales
    approximately with mass**0.75. It is deliberately a model, not a claim that
    every species follows one exact exponent.
    """

    body_mass_kg: float
    metabolic_coefficient_w_per_kg075: float = 3.5
    body_temperature_c: float = 37.0

    def __post_init__(self) -> None:
        if self.body_mass_kg <= 0:
            raise ValueError("body_mass_kg must be positive")
        if self.metabolic_coefficient_w_per_kg075 <= 0:
            raise ValueError("metabolic coefficient must be positive")

    @property
    def basal_power_watts(self) -> float:
        return self.metabolic_coefficient_w_per_kg075 * self.body_mass_kg**0.75

    def energy_required_joules(self, seconds: float, activity_factor: float = 1.0) -> float:
        if seconds < 0 or activity_factor < 0:
            raise ValueError("seconds and activity_factor cannot be negative")
        return self.basal_power_watts * activity_factor * seconds

    def thermal_stress(self, ambient_c: float, comfort_range_c: float = 20.0) -> float:
        if comfort_range_c <= 0:
            raise ValueError("comfort range must be positive")
        return max(0.0, abs(ambient_c - self.body_temperature_c) - comfort_range_c) / comfort_range_c
