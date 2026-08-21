from __future__ import annotations

from dataclasses import dataclass, field
import math

from .types import Biome, GeoCell


@dataclass(slots=True)
class Geography:
    """Sparse deterministic geography with bounded neighborhood queries."""

    cells: dict[tuple[int, int], GeoCell] = field(default_factory=dict)

    def add(self, cell: GeoCell) -> None:
        key = (cell.x, cell.y)
        if key in self.cells:
            raise ValueError(f"Geographic cell already exists: {key}")
        self.cells[key] = cell

    def get(self, x: int, y: int) -> GeoCell | None:
        return self.cells.get((x, y))

    def neighbors(self, x: int, y: int, radius: int = 1) -> tuple[GeoCell, ...]:
        if radius < 0:
            raise ValueError("radius cannot be negative")
        result: list[GeoCell] = []
        for cell in self.cells.values():
            if cell.x == x and cell.y == y:
                continue
            if max(abs(cell.x - x), abs(cell.y - y)) <= radius:
                result.append(cell)
        return tuple(sorted(result, key=lambda c: (c.x, c.y)))

    def climate_biome(self, latitude: float, elevation_m: float, moisture: float) -> Biome:
        """Classify a cell using replaceable, intentionally simple climate rules."""
        if not -90 <= latitude <= 90:
            raise ValueError("latitude must be between -90 and 90")
        if moisture < 0:
            raise ValueError("moisture cannot be negative")
        abs_lat = abs(latitude)
        temperature = 30.0 * (1.0 - abs_lat / 90.0) - max(elevation_m, 0.0) * 0.0065
        if temperature < -2:
            return Biome.TUNDRA
        if elevation_m > 2500:
            return Biome.MOUNTAIN
        if moisture < 0.15:
            return Biome.DESERT
        if moisture > 0.8:
            return Biome.WETLAND
        if moisture > 0.55:
            return Biome.FOREST
        if temperature > 18:
            return Biome.GRASSLAND
        return Biome.PLAINS
