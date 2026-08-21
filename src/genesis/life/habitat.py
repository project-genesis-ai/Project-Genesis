from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class HabitatCell:
    """A spatial ecological cell with resources and environmental capacity."""

    cell_id: str
    x: int
    y: int
    biome: str = "temperate_forest"
    vegetation: float = 1.0
    water: float = 1.0
    shelter: float = 1.0
    carrying_capacity: float = 100.0

    def __post_init__(self) -> None:
        if not self.cell_id.strip():
            raise ValueError("cell_id cannot be empty")
        if self.carrying_capacity < 0.0:
            raise ValueError("carrying_capacity cannot be negative")
        for name in ("vegetation", "water", "shelter"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")

    def consume_vegetation(self, amount: float) -> float:
        if amount < 0.0:
            raise ValueError("amount cannot be negative")
        consumed = min(self.vegetation, amount)
        self.vegetation -= consumed
        return consumed

    def consume_water(self, amount: float) -> float:
        if amount < 0.0:
            raise ValueError("amount cannot be negative")
        consumed = min(self.water, amount)
        self.water -= consumed
        return consumed


@dataclass(slots=True)
class HabitatMap:
    """Sparse deterministic grid used by organisms and environmental systems."""

    cells: dict[tuple[int, int], HabitatCell] = field(default_factory=dict)

    def add(self, cell: HabitatCell) -> None:
        key = (cell.x, cell.y)
        if key in self.cells:
            raise ValueError(f"Habitat cell already exists: {key}")
        self.cells[key] = cell

    def get(self, x: int, y: int) -> HabitatCell | None:
        return self.cells.get((x, y))

    def neighbors(self, x: int, y: int, radius: int = 1) -> tuple[HabitatCell, ...]:
        if radius < 0:
            raise ValueError("radius cannot be negative")
        result: list[HabitatCell] = []
        for cell in self.cells.values():
            if max(abs(cell.x - x), abs(cell.y - y)) <= radius and (cell.x, cell.y) != (x, y):
                result.append(cell)
        return tuple(sorted(result, key=lambda item: (item.y, item.x)))
