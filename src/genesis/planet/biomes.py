from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BiomeState:
    name: str
    vegetation_productivity: float
    soil_moisture: float
    carrying_capacity: float
    freshwater_suitability: float

    def __post_init__(self) -> None:
        for value in (self.vegetation_productivity, self.soil_moisture, self.carrying_capacity, self.freshwater_suitability):
            if value < 0:
                raise ValueError("biome values cannot be negative")


class BiomeEngine:
    """Continuous climate-to-biome classification instead of painted biome labels."""

    def classify(self, *, temperature_c: float, precipitation_mm: float, elevation_m: float,
                 soil_moisture: float, freshwater: bool = False) -> BiomeState:
        if precipitation_mm < 0 or soil_moisture < 0:
            raise ValueError("precipitation and soil moisture cannot be negative")
        if freshwater:
            name = "freshwater"
            productivity = min(1.0, 0.35 + precipitation_mm / 250.0 + soil_moisture * 0.3)
            capacity = 1.5 * productivity
        elif elevation_m > 3500 or temperature_c < -12:
            name = "alpine_tundra" if elevation_m > 3500 else "tundra"
            productivity = max(0.02, 0.18 - max(0.0, -temperature_c - 5.0) * 0.01)
            capacity = 0.4 * productivity
        elif precipitation_mm > 180 and temperature_c > 22:
            name = "rainforest"
            productivity = 1.0
            capacity = 2.8
        elif precipitation_mm < 25 and temperature_c > 18:
            name = "desert"
            productivity = max(0.03, 0.14 - precipitation_mm * 0.002)
            capacity = 0.35
        elif precipitation_mm > 110 and temperature_c > 5:
            name = "temperate_forest" if temperature_c < 24 else "tropical_forest"
            productivity = min(0.95, 0.52 + precipitation_mm / 450.0)
            capacity = 2.2 * productivity
        elif precipitation_mm > 65 and temperature_c > 8:
            name = "grassland"
            productivity = min(0.82, 0.38 + precipitation_mm / 250.0)
            capacity = 1.8 * productivity
        elif precipitation_mm > 70:
            name = "wetland"
            productivity = min(0.9, 0.55 + precipitation_mm / 500.0)
            capacity = 2.0 * productivity
        else:
            name = "boreal"
            productivity = max(0.08, 0.32 + precipitation_mm / 500.0)
            capacity = 1.2 * productivity
        freshwater_suitability = min(1.0, soil_moisture * 0.7 + precipitation_mm / 300.0)
        return BiomeState(name, productivity, soil_moisture, capacity, freshwater_suitability)
