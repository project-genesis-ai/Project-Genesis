from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

class ResourceType(StrEnum):
    WATER = "water"
    FOOD = "food"
    WOOD = "wood"
    STONE = "stone"
    ORE = "ore"
    METAL = "metal"
    ENERGY = "energy"

@dataclass(slots=True)
class ResourceStock:
    """Mass/energy inventories with explicit non-negative quantities."""
    quantities: dict[ResourceType, float] = field(default_factory=dict)

    def amount(self, resource: ResourceType) -> float:
        return self.quantities.get(resource, 0.0)

    def add(self, resource: ResourceType, quantity: float) -> None:
        if quantity < 0.0:
            raise ValueError("quantity cannot be negative")
        self.quantities[resource] = self.amount(resource) + quantity

    def remove(self, resource: ResourceType, quantity: float) -> None:
        if quantity < 0.0:
            raise ValueError("quantity cannot be negative")
        available = self.amount(resource)
        if quantity > available:
            raise ValueError("insufficient resource")
        self.quantities[resource] = available - quantity

    def transfer_to(self, other: ResourceStock, resource: ResourceType, quantity: float) -> None:
        self.remove(resource, quantity)
        other.add(resource, quantity)
