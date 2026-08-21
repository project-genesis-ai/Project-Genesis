import pytest

from genesis.civilization.government import Government
from genesis.economy.inventory import Inventory
from genesis.economy.market import Market
from genesis.economy.trade import Trade


def test_inventory_transfer() -> None:
    seller = Inventory({"food": 5.0})
    buyer = Inventory()
    Trade("buyer", "seller", "food", 2.0, 3.0).execute(buyer, seller)
    assert seller.quantity("food") == 3.0
    assert buyer.quantity("food") == 2.0


def test_inventory_rejects_overdraw() -> None:
    with pytest.raises(ValueError):
        Inventory({"food": 1.0}).remove("food", 2.0)


def test_market_price_responds_to_demand() -> None:
    market = Market()
    market.set_price("food", 10.0)
    market.record_supply("food", 1.0)
    market.record_demand("food", 5.0)
    assert market.rebalance("food") > 10.0


def test_government_treasury() -> None:
    government = Government("g", "Settlement")
    government.collect_tax(5.0)
    assert government.treasury == 5.0
