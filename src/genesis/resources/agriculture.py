from __future__ import annotations

from dataclasses import dataclass
import math

from .stock import ResourceStock, ResourceType

@dataclass(frozen=True, slots=True)
class Crop:
    crop_id: str
    name: str
    growth_days: float
    optimal_temperature_c: float
    temperature_tolerance_c: float
    water_need_mm: float
    yield_kg_per_m2: float
    seed_mass_kg_per_m2: float = 0.01

    def __post_init__(self) -> None:
        if self.growth_days <= 0 or self.temperature_tolerance_c <= 0 or self.water_need_mm < 0 or self.yield_kg_per_m2 < 0:
            raise ValueError("crop physical parameters are invalid")

@dataclass(slots=True)
class Field:
    field_id: str
    area_m2: float
    crop: Crop
    age_days: float = 0.0
    water_received_mm: float = 0.0
    harvested: bool = False

    def __post_init__(self) -> None:
        if self.area_m2 <= 0:
            raise ValueError("field area must be positive")

    @property
    def maturity(self) -> float:
        return min(1.0, self.age_days / self.crop.growth_days)

    def grow(self, days: float, temperature_c: float, rainfall_mm: float) -> float:
        if days < 0 or rainfall_mm < 0:
            raise ValueError("growth inputs cannot be negative")
        if self.harvested:
            return 0.0
        thermal = max(0.0, 1.0 - abs(temperature_c - self.crop.optimal_temperature_c) / self.crop.temperature_tolerance_c)
        self.age_days = min(self.crop.growth_days, self.age_days + days * thermal)
        self.water_received_mm += rainfall_mm
        return thermal

    def harvest(self) -> float:
        if self.harvested or self.maturity < 1.0:
            return 0.0
        self.harvested = True
        return self.area_m2 * self.crop.yield_kg_per_m2

@dataclass(slots=True)
class FarmSystem:
    fields: dict[str, Field]
    stock: ResourceStock

    def step(self, days: float, temperature_c: float, rainfall_mm: float) -> None:
        if days < 0:
            raise ValueError("days cannot be negative")
        for field in self.fields.values():
            field.grow(days, temperature_c, rainfall_mm)

    def harvest_ready(self) -> float:
        total = 0.0
        for field in self.fields.values():
            yield_kg = field.harvest()
            if yield_kg:
                self.stock.add(ResourceType.FOOD, yield_kg)
                total += yield_kg
        return total
