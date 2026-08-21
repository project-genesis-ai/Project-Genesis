from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Inventory:
    items: dict[str, float] = field(default_factory=dict)

    def quantity(self, item: str) -> float:
        return self.items.get(item, 0.0)

    def add(self, item: str, quantity: float) -> None:
        if quantity < 0:
            raise ValueError("quantity cannot be negative")
        self.items[item] = self.quantity(item) + quantity

    def remove(self, item: str, quantity: float) -> None:
        if quantity < 0 or self.quantity(item) + 1e-12 < quantity:
            raise ValueError("insufficient inventory")
        remaining = self.quantity(item) - quantity
        if remaining <= 1e-12:
            self.items.pop(item, None)
        else:
            self.items[item] = remaining
