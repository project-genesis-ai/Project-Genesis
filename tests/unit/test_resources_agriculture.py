import pytest
from genesis.resources import Crop, Field, FarmSystem, ResourceStock, ResourceType

def test_resource_transfer_preserves_quantity():
    a, b = ResourceStock(), ResourceStock()
    a.add(ResourceType.WATER, 100.0)
    a.transfer_to(b, ResourceType.WATER, 30.0)
    assert a.amount(ResourceType.WATER) == pytest.approx(70.0)
    assert b.amount(ResourceType.WATER) == pytest.approx(30.0)

def test_resource_transfer_is_atomic_on_insufficient_stock():
    a, b = ResourceStock(), ResourceStock()
    a.add(ResourceType.WATER, 5.0)
    with pytest.raises(ValueError):
        a.transfer_to(b, ResourceType.WATER, 6.0)
    assert a.amount(ResourceType.WATER) == 5.0
    assert b.amount(ResourceType.WATER) == 0.0

def test_crop_growth_depends_on_temperature():
    crop = Crop("wheat", "Wheat", 100, 20, 10, 400, 0.8)
    field = Field("f", 100, crop)
    field.grow(10, 20, 20)
    assert field.age_days == pytest.approx(10)
    field.grow(10, 40, 20)
    assert field.age_days == pytest.approx(10)

def test_harvest_adds_mass_to_food_stock():
    crop = Crop("rice", "Rice", 10, 25, 10, 100, 1.0)
    field = Field("f", 100, crop)
    farm = FarmSystem({"f": field}, ResourceStock())
    farm.step(10, 25, 100)
    assert farm.harvest_ready() == pytest.approx(100.0)
    assert farm.stock.amount(ResourceType.FOOD) == pytest.approx(100.0)
