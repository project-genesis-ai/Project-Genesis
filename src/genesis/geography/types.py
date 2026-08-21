from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Biome(str, Enum):
    OCEAN = "ocean"
    MOUNTAIN = "mountain"
    DESERT = "desert"
    FOREST = "forest"
    GRASSLAND = "grassland"
    WETLAND = "wetland"
    TUNDRA = "tundra"
    PLAINS = "plains"


@dataclass(frozen=True, slots=True)
class GeoCell:
    """Deterministic geographic cell used by world-scale systems."""

    x: int
    y: int
    elevation_m: float
    latitude: float
    biome: Biome
    soil_fertility: float = 0.0
    water: float = 0.0

    def __post_init__(self) -> None:
        if not -90.0 <= self.latitude <= 90.0:
            raise ValueError("latitude must be between -90 and 90")
        if self.soil_fertility < 0 or self.water < 0:
            raise ValueError("soil fertility and water cannot be negative")
