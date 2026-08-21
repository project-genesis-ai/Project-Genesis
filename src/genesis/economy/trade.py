from __future__ import annotations

from dataclasses import dataclass

from .inventory import Inventory


@dataclass(frozen=True, slots=True)
class Trade:
    buyer_id: str
    seller_id: str
    item: str
    quantity: float
    unit_price: float

    @property
    def total(self) -> float:
        return self.quantity * self.unit_price

    def execute(self, buyer: Inventory, seller: Inventory) -> None:
        if self.quantity <= 0 or self.unit_price < 0:
            raise ValueError("trade quantity must be positive and price non-negative")
        seller.remove(self.item, self.quantity)
        buyer.add(self.item, self.quantity)
