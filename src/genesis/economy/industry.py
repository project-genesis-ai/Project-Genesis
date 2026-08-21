from __future__ import annotations

from dataclasses import dataclass

from genesis.physics import Energy
from genesis.resources import ResourceStock, ResourceType

@dataclass(frozen=True, slots=True)
class IndustrialRecipe:
    recipe_id: str
    inputs: dict[ResourceType, float]
    outputs: dict[ResourceType, float]
    energy_joules: float = 0.0

    def __post_init__(self) -> None:
        if not self.recipe_id.strip():
            raise ValueError("recipe_id cannot be empty")
        if self.energy_joules < 0 or any(v <= 0 for v in (*self.inputs.values(), *self.outputs.values())):
            raise ValueError("recipe quantities and energy must be non-negative")

@dataclass(slots=True)
class IndustrialPlant:
    plant_id: str
    recipe: IndustrialRecipe
    efficiency: float = 1.0

    def __post_init__(self) -> None:
        if not self.plant_id.strip() or not 0.0 < self.efficiency <= 1.0:
            raise ValueError("invalid plant configuration")

    def run(self, stock: ResourceStock, available_energy: Energy) -> Energy:
        if available_energy.joules < self.recipe.energy_joules:
            raise ValueError("insufficient process energy")
        for resource, quantity in self.recipe.inputs.items():
            if stock.amount(resource) < quantity:
                raise ValueError("insufficient material input")
        for resource, quantity in self.recipe.inputs.items():
            stock.remove(resource, quantity)
        for resource, quantity in self.recipe.outputs.items():
            stock.add(resource, quantity * self.efficiency)
        return Energy(self.recipe.energy_joules)
