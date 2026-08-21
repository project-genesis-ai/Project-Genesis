from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class FarmState(str, Enum):
    PREPARED = "prepared"
    PLANTED = "planted"
    GROWING = "growing"
    READY = "ready"
    HARVESTED = "harvested"


@dataclass(frozen=True, slots=True)
class Crop:
    crop_id: str
    name: str
    growth_ticks: int
    yield_per_area: float
    water_need: float = 0.5

    def __post_init__(self) -> None:
        if not self.crop_id.strip() or not self.name.strip():
            raise ValueError("crop identity cannot be empty")
        if self.growth_ticks < 1 or self.yield_per_area < 0 or not 0 <= self.water_need <= 1:
            raise ValueError("invalid crop parameters")


@dataclass(slots=True)
class Farm:
    farm_id: str
    crop: Crop
    area: float
    soil_fertility: float = 1.0
    water: float = 1.0
    state: FarmState = FarmState.PREPARED
    age_ticks: int = 0
    harvest_history: list[float] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.farm_id.strip() or self.area <= 0:
            raise ValueError("invalid farm identity or area")
        if not 0 <= self.soil_fertility <= 1 or not 0 <= self.water <= 1:
            raise ValueError("soil fertility and water must be between 0 and 1")

    def plant(self) -> None:
        if self.state not in (FarmState.PREPARED, FarmState.HARVESTED):
            raise ValueError("farm is not ready for planting")
        self.age_ticks = 0
        self.state = FarmState.PLANTED

    def step(self, ticks: int = 1, rainfall: float = 0.0) -> None:
        if ticks < 0 or rainfall < 0:
            raise ValueError("ticks and rainfall cannot be negative")
        if self.state in (FarmState.PLANTED, FarmState.GROWING):
            self.water = min(1.0, self.water + rainfall)
            self.age_ticks += ticks
            consumed = min(self.water, self.crop.water_need * ticks / max(1, self.crop.growth_ticks))
            self.water -= consumed
            self.state = FarmState.READY if self.age_ticks >= self.crop.growth_ticks else FarmState.GROWING

    def harvest(self) -> float:
        if self.state is not FarmState.READY:
            raise ValueError("crop is not ready for harvest")
        yield_amount = self.area * self.crop.yield_per_area * self.soil_fertility * (0.5 + 0.5 * self.water)
        self.harvest_history.append(yield_amount)
        self.soil_fertility = max(0.0, self.soil_fertility - min(0.2, self.area * 0.001))
        self.state = FarmState.HARVESTED
        return yield_amount
