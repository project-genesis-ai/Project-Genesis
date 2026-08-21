from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SettlementType(str, Enum):
    CAMP = "camp"
    VILLAGE = "village"
    TOWN = "town"
    CITY = "city"


class BuildingType(str, Enum):
    HOME = "home"
    FARM = "farm"
    MARKET = "market"
    SCHOOL = "school"
    WORKSHOP = "workshop"
    STORAGE = "storage"
    HOSPITAL = "hospital"


@dataclass(slots=True)
class Building:
    building_id: str
    kind: BuildingType
    capacity: int = 1
    condition: float = 1.0
    occupants: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.building_id.strip():
            raise ValueError("building_id cannot be empty")
        if self.capacity < 1 or not 0.0 <= self.condition <= 1.0:
            raise ValueError("capacity or condition is invalid")

    def add_occupant(self, agent_id: str) -> bool:
        if not agent_id.strip():
            raise ValueError("agent_id cannot be empty")
        if len(self.occupants) >= self.capacity and agent_id not in self.occupants:
            return False
        self.occupants.add(agent_id)
        return True

    def maintain(self, amount: float) -> None:
        if amount < 0:
            raise ValueError("maintenance cannot be negative")
        self.condition = min(1.0, self.condition + amount)

    def degrade(self, amount: float) -> None:
        if amount < 0:
            raise ValueError("degradation cannot be negative")
        self.condition = max(0.0, self.condition - amount)


@dataclass(slots=True)
class Settlement:
    settlement_id: str
    name: str
    kind: SettlementType = SettlementType.CAMP
    population: set[str] = field(default_factory=set)
    buildings: dict[str, Building] = field(default_factory=dict)
    stored_resources: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.settlement_id.strip() or not self.name.strip():
            raise ValueError("settlement identity cannot be empty")

    def add_resident(self, agent_id: str) -> None:
        if not agent_id.strip():
            raise ValueError("agent_id cannot be empty")
        self.population.add(agent_id)

    def add_building(self, building: Building) -> None:
        if building.building_id in self.buildings:
            raise ValueError(f"building already exists: {building.building_id}")
        self.buildings[building.building_id] = building

    def store(self, resource: str, amount: float) -> None:
        if not resource.strip() or amount < 0:
            raise ValueError("resource and non-negative amount are required")
        self.stored_resources[resource] = self.stored_resources.get(resource, 0.0) + amount

    def withdraw(self, resource: str, amount: float) -> bool:
        if amount < 0:
            raise ValueError("amount cannot be negative")
        available = self.stored_resources.get(resource, 0.0)
        if available < amount:
            return False
        self.stored_resources[resource] = available - amount
        return True

    def auto_upgrade(self) -> bool:
        thresholds = {
            SettlementType.CAMP: (10, SettlementType.VILLAGE),
            SettlementType.VILLAGE: (100, SettlementType.TOWN),
            SettlementType.TOWN: (1000, SettlementType.CITY),
        }
        rule = thresholds.get(self.kind)
        if rule and len(self.population) >= rule[0]:
            self.kind = rule[1]
            return True
        return False
