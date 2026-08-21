from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class AquaticCell:
    """Water-column state for lakes, rivers and ocean cells."""

    salinity: float = 0.0
    dissolved_oxygen: float = 1.0
    nutrients: float = 0.5
    depth_m: float = 10.0
    temperature_c: float = 15.0
    biomass: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0 <= self.salinity <= 1:
            raise ValueError("salinity must be between 0 and 1")
        if not 0 <= self.dissolved_oxygen <= 1 or self.nutrients < 0 or self.depth_m < 0:
            raise ValueError("invalid aquatic state")
        if self.temperature_c < -5:
            raise ValueError("temperature is below supported water range")

    def primary_production(self, light: float) -> float:
        if not 0 <= light <= 1:
            raise ValueError("light must be between 0 and 1")
        phytoplankton = min(self.nutrients, light * self.dissolved_oxygen * 0.2)
        self.biomass["phytoplankton"] = self.biomass.get("phytoplankton", 0.0) + phytoplankton
        self.nutrients = max(0.0, self.nutrients - phytoplankton * 0.5)
        return phytoplankton

    def turnover(self, decomposition: float = 0.05) -> None:
        if decomposition < 0:
            raise ValueError("decomposition cannot be negative")
        dead = sum(amount for name, amount in self.biomass.items() if name.endswith("_detritus"))
        self.nutrients += dead * decomposition
        self.dissolved_oxygen = max(0.0, self.dissolved_oxygen - dead * decomposition * 0.02)


class AquaticSystem:
    """Lightweight full aquatic food-web substrate from plankton to predators."""

    def __init__(self) -> None:
        self.cells: dict[tuple[int, int], AquaticCell] = {}

    def add_cell(self, x: int, y: int, cell: AquaticCell) -> None:
        self.cells[(x, y)] = cell

    def step(self, sunlight: float = 0.6) -> None:
        for cell in self.cells.values():
            produced = cell.primary_production(sunlight)
            zoo = min(cell.biomass.get("phytoplankton", 0.0), produced * 0.55)
            cell.biomass["zooplankton"] = cell.biomass.get("zooplankton", 0.0) + zoo
            cell.biomass["phytoplankton"] = max(0.0, cell.biomass.get("phytoplankton", 0.0) - zoo)
            fish = min(cell.biomass.get("zooplankton", 0.0), zoo * 0.35)
            cell.biomass["fish"] = cell.biomass.get("fish", 0.0) + fish
            cell.biomass["zooplankton"] = max(0.0, cell.biomass.get("zooplankton", 0.0) - fish)
            predator = min(cell.biomass.get("fish", 0.0), fish * 0.2)
            cell.biomass["apex_predator"] = cell.biomass.get("apex_predator", 0.0) + predator
            cell.biomass["fish"] = max(0.0, cell.biomass.get("fish", 0.0) - predator)
            cell.turnover()
