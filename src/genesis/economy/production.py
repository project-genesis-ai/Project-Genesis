from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProductionRecipe:
    recipe_id: str
    inputs: dict[str, float]
    outputs: dict[str, float]
    work_ticks: int = 1

    def __post_init__(self) -> None:
        if not self.recipe_id.strip():
            raise ValueError("recipe_id cannot be empty")
        if self.work_ticks < 1:
            raise ValueError("work_ticks must be positive")
        if any(value <= 0 for value in (*self.inputs.values(), *self.outputs.values())):
            raise ValueError("recipe quantities must be positive")

    def can_produce(self, inventory: dict[str, float]) -> bool:
        return all(inventory.get(item, 0.0) >= quantity for item, quantity in self.inputs.items())

    def produce(self, inventory: dict[str, float]) -> None:
        if not self.can_produce(inventory):
            raise ValueError("insufficient inputs")
        for item, quantity in self.inputs.items():
            inventory[item] -= quantity
        for item, quantity in self.outputs.items():
            inventory[item] = inventory.get(item, 0.0) + quantity
