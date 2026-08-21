from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Market:
    prices: dict[str, float] = field(default_factory=dict)
    supply: dict[str, float] = field(default_factory=dict)
    demand: dict[str, float] = field(default_factory=dict)

    def set_price(self, item: str, price: float) -> None:
        if price < 0:
            raise ValueError("price cannot be negative")
        self.prices[item] = price

    def price(self, item: str) -> float:
        return self.prices.get(item, 0.0)

    def record_supply(self, item: str, quantity: float) -> None:
        if quantity < 0:
            raise ValueError("quantity cannot be negative")
        self.supply[item] = self.supply.get(item, 0.0) + quantity

    def record_demand(self, item: str, quantity: float) -> None:
        if quantity < 0:
            raise ValueError("quantity cannot be negative")
        self.demand[item] = self.demand.get(item, 0.0) + quantity

    def rebalance(self, item: str, sensitivity: float = 0.05) -> float:
        if sensitivity < 0:
            raise ValueError("sensitivity cannot be negative")
        old = self.price(item)
        supply = self.supply.get(item, 0.0)
        demand = self.demand.get(item, 0.0)
        if old == 0.0:
            old = 1.0
        ratio = (demand - supply) / max(1.0, supply + demand)
        new = max(0.0, old * (1.0 + sensitivity * ratio))
        self.prices[item] = new
        return new
