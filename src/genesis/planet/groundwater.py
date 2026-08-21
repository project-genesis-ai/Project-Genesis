from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GroundwaterState:
    storage_mm: float = 0.0
    recharge_mm: float = 0.0
    discharge_mm: float = 0.0
    water_table_m: float = 0.0

    def __post_init__(self) -> None:
        if min(self.storage_mm, self.recharge_mm, self.discharge_mm, self.water_table_m) < 0:
            raise ValueError("groundwater values cannot be negative")


class GroundwaterEngine:
    """Simple aquifer store coupling infiltration to springs and groundwater discharge."""

    def __init__(self, specific_yield: float = 0.25, discharge_rate: float = 0.03) -> None:
        if not 0 < specific_yield <= 1 or not 0 <= discharge_rate <= 1:
            raise ValueError("invalid groundwater parameters")
        self.specific_yield = specific_yield
        self.discharge_rate = discharge_rate

    def step(self, state: GroundwaterState, *, recharge_mm: float, aquifer_capacity_mm: float,
             demand_mm: float = 0.0) -> GroundwaterState:
        if recharge_mm < 0 or aquifer_capacity_mm < 0 or demand_mm < 0:
            raise ValueError("groundwater inputs cannot be negative")
        stored = min(aquifer_capacity_mm, state.storage_mm + recharge_mm)
        natural_discharge = min(stored, stored * self.discharge_rate)
        extraction = min(stored - natural_discharge, demand_mm)
        next_storage = max(0.0, stored - natural_discharge - extraction)
        recharge = max(0.0, stored - state.storage_mm)
        water_table = next_storage / max(1e-6, aquifer_capacity_mm) / self.specific_yield * 10.0
        return GroundwaterState(next_storage, recharge, natural_discharge + extraction, water_table)
