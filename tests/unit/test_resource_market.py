import pytest
from genesis.economy.resource_market import ResourceMarket
from genesis.resources import ResourceStock, ResourceType

def test_resource_market_conserves_inventory():
    seller, buyer = ResourceStock(), ResourceStock()
    seller.add(ResourceType.FOOD, 50)
    trade = ResourceMarket().settle(seller, buyer, ResourceType.FOOD, 12.5, 4.0)
    assert trade.total_value == pytest.approx(50.0)
    assert seller.amount(ResourceType.FOOD) == pytest.approx(37.5)
    assert buyer.amount(ResourceType.FOOD) == pytest.approx(12.5)
