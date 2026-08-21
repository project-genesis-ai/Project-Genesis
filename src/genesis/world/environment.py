from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Biome(StrEnum):
    FOREST = "forest"
    GRASSLAND = "grassland"
    DESERT = "desert"
    WETLAND = "wetland"
    TUNDRA = "tundra"
    OCEAN = "ocean"


@dataclass(slots=True)
class EnvironmentCell:
    """Environmental state that can drive organisms and future climate systems."""

    cell_id: str
    biome: Biome
    elevation_m: float = 0.0
    temperature_c: float = 20.0
    rainfall_mm: float = 0.0
    water_mm: float = 0.0
    vegetation: float = 0.0

    def __post_init__(self) -> None:
        if not self.cell_id.strip():
            raise ValueError("cell_id cannot be empty")
        if not 0.0 <= self.vegetation <= 1.0:
            raise ValueError("vegetation must be between 0 and 1")
        if self.rainfall_mm < 0.0 or self.water_mm < 0.0:
            raise ValueError("water quantities cannot be negative")


@dataclass(slots=True)
class Environment:
    cells: dict[str, EnvironmentCell] = field(default_factory=dict)

    def add_cell(self, cell: EnvironmentCell) -> None:
        if cell.cell_id in self.cells:
            raise ValueError(f"Environment cell already exists: {cell.cell_id}")
        self.cells[cell.cell_id] = cell

    def cell(self, cell_id: str) -> EnvironmentCell:
        try:
            return self.cells[cell_id]
        except KeyError as exc:
            raise KeyError(f"Unknown environment cell: {cell_id}") from exc
