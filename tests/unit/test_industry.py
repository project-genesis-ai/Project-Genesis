import pytest
from genesis.economy import IndustrialPlant, IndustrialRecipe
from genesis.physics import Energy
from genesis.resources import ResourceStock, ResourceType

def test_industry_converts_material_with_efficiency():
    stock = ResourceStock()
    stock.add(ResourceType.ORE, 10.0)
    recipe = IndustrialRecipe("smelt", {ResourceType.ORE: 10.0}, {ResourceType.METAL: 8.0}, 5000.0)
    plant = IndustrialPlant("forge", recipe, efficiency=0.75)
    consumed = plant.run(stock, Energy(5000.0))
    assert consumed.joules == pytest.approx(5000.0)
    assert stock.amount(ResourceType.ORE) == pytest.approx(0.0)
    assert stock.amount(ResourceType.METAL) == pytest.approx(6.0)

def test_industry_preflights_inputs_without_mutating_on_failure():
    stock = ResourceStock()
    stock.add(ResourceType.ORE, 2.0)
    recipe = IndustrialRecipe("smelt", {ResourceType.ORE: 3.0}, {ResourceType.METAL: 1.0})
    with pytest.raises(ValueError):
        IndustrialPlant("forge", recipe).run(stock, Energy(0.0))
    assert stock.amount(ResourceType.ORE) == pytest.approx(2.0)
