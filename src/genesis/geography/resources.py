from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ResourceStock:
    """Renewable/non-renewable resource stock with explicit regeneration."""

    amount: float = 0.0
    capacity: float = 0.0
    regeneration_per_tick: float = 0.0

    def __post_init__(self) -> None:
        if self.amount < 0 or self.capacity < 0 or self.regeneration_per_tick < 0:
            raise ValueError("resource values cannot be negative")
        if self.amount > self.capacity:
            raise ValueError("amount cannot exceed capacity")

    def harvest(self, amount: float) -> float:
        if amount < 0:
            raise ValueError("harvest amount cannot be negative")
        taken = min(amount, self.amount)
        self.amount -= taken
        return taken

    def regenerate(self, ticks: int = 1) -> None:
        if ticks < 0:
            raise ValueError("ticks cannot be negative")
        self.amount = min(self.capacity, self.amount + self.regeneration_per_tick * ticks)


@dataclass(slots=True)
class ResourceField:
    stocks: dict[str, ResourceStock] = field(default_factory=dict)

    def add(self, name: str, stock: ResourceStock) -> None:
        if not name:
            raise ValueError("resource name cannot be empty")
        if name in self.stocks:
            raise ValueError(f"resource already exists: {name}")
        self.stocks[name] = stock

    def step(self, ticks: int = 1) -> None:
        for stock in self.stocks.values():
            stock.regenerate(ticks)
