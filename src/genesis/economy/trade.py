from __future__ import annotations

from dataclasses import dataclass

from .inventory import Inventory
from .wallet import Wallet


@dataclass(frozen=True, slots=True)
class Trade:
    buyer_id: str
    seller_id: str
    item: str
    quantity: float
    unit_price: float

    def __post_init__(self) -> None:
        if not self.buyer_id.strip() or not self.seller_id.strip() or not self.item.strip():
            raise ValueError("trade identities cannot be empty")
        if self.quantity <= 0 or self.unit_price < 0:
            raise ValueError("trade quantity must be positive and price non-negative")
        if self.buyer_id == self.seller_id:
            raise ValueError("buyer and seller must differ")

    @property
    def total(self) -> float:
        return self.quantity * self.unit_price

    def execute(self, buyer: Inventory, seller: Inventory) -> None:
        seller.remove(self.item, self.quantity)
        buyer.add(self.item, self.quantity)

    def execute_with_money(self, buyer: Inventory, seller: Inventory, buyer_wallet: Wallet, seller_wallet: Wallet) -> bool:
        if buyer_wallet.owner_id != self.buyer_id or seller_wallet.owner_id != self.seller_id:
            raise ValueError("wallet owners do not match trade participants")
        if not seller.remove(self.item, self.quantity):
            return False
        if not buyer_wallet.transfer_to(seller_wallet, self.total):
            seller.add(self.item, self.quantity)
            return False
        buyer.add(self.item, self.quantity)
        return True
