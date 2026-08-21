from __future__ import annotations

from dataclasses import dataclass

from genesis.resources import ResourceStock, ResourceType

@dataclass(frozen=True, slots=True)
class ResourceTrade:
    resource: ResourceType
    quantity: float
    unit_price: float
    total_value: float

class ResourceMarket:
    """Conserves physical inventory while settling its monetary counterpart."""
    def quote(self, stock: ResourceStock, resource: ResourceType, quantity: float, unit_price: float) -> ResourceTrade:
        if quantity < 0 or unit_price < 0:
            raise ValueError("quantity and price cannot be negative")
        if quantity > stock.amount(resource):
            raise ValueError("insufficient inventory")
        return ResourceTrade(resource, quantity, unit_price, quantity * unit_price)

    def settle(self, seller: ResourceStock, buyer: ResourceStock, resource: ResourceType, quantity: float, unit_price: float) -> ResourceTrade:
        trade = self.quote(seller, resource, quantity, unit_price)
        seller.transfer_to(buyer, resource, quantity)
        return trade
