from genesis.agents.agent import Agent
from genesis.agents.perception import perceive
from genesis.economy.production import ProductionRecipe
from genesis.society.settlements import Settlement
from genesis.world.world import WorldState


def test_perception_only_returns_available_resources() -> None:
    world = WorldState(resources={"water": 10.0, "empty": 0.0})
    perception = perceive(Agent("a", "A"), world, 0)
    assert perception.nearby_resources == ("water",)


def test_production_consumes_inputs_and_creates_outputs() -> None:
    inventory = {"wood": 2.0}
    ProductionRecipe("stick", {"wood": 1.0}, {"stick": 2.0}).produce(inventory)
    assert inventory == {"wood": 1.0, "stick": 2.0}


def test_settlement_population_is_unique() -> None:
    settlement = Settlement("s", "First Settlement")
    settlement.add_resident("a")
    settlement.add_resident("a")
    assert settlement.population_count == 1
