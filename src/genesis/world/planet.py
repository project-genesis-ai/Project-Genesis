from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from math import exp


class Terrain(StrEnum):
    OCEAN = "ocean"
    COAST = "coast"
    PLAINS = "plains"
    FOREST = "forest"
    MOUNTAIN = "mountain"
    DESERT = "desert"
    POLAR = "polar"


class EnvironmentType(StrEnum):
    LAND = "land"
    OCEAN = "ocean"
    SPACE = "space"


@dataclass(slots=True)
class Atmosphere:
    """Local atmosphere; values are physical fractions/partial pressures."""

    oxygen_fraction: float = 0.2095
    pressure_kpa: float = 101.325
    carbon_dioxide_ppm: float = 420.0
    nitrogen_fraction: float = 0.7808
    pollutants_index: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.oxygen_fraction <= 1.0:
            raise ValueError("oxygen_fraction must be between 0 and 1")
        if self.pressure_kpa < 0 or self.carbon_dioxide_ppm < 0 or self.pollutants_index < 0:
            raise ValueError("atmospheric quantities cannot be negative")

    @property
    def oxygen_partial_pressure_kpa(self) -> float:
        return self.pressure_kpa * self.oxygen_fraction

    @property
    def breathable_for_humans(self) -> bool:
        return self.pressure_kpa >= 50.0 and self.oxygen_partial_pressure_kpa >= 12.0


@dataclass(slots=True)
class OceanWater:
    """Aquatic environment; dissolved oxygen is distinct from atmospheric oxygen."""

    depth_m: float = 100.0
    temperature_c: float = 15.0
    salinity_ppt: float = 35.0
    dissolved_oxygen_mg_l: float = 8.0
    pollution_index: float = 0.0

    def __post_init__(self) -> None:
        if self.depth_m < 0 or self.salinity_ppt < 0 or self.dissolved_oxygen_mg_l < 0 or self.pollution_index < 0:
            raise ValueError("ocean values cannot be negative")

    @property
    def supports_fish(self) -> bool:
        return self.dissolved_oxygen_mg_l >= 2.0 and self.pollution_index < 0.95

    @property
    def supports_human_breathing(self) -> bool:
        return False


@dataclass(slots=True)
class GravityField:
    surface_g: float = 9.80665

    def __post_init__(self) -> None:
        if self.surface_g <= 0:
            raise ValueError("gravity must be positive")

    def acceleration(self, altitude_m: float = 0.0, planet_radius_m: float = 6_371_000.0) -> float:
        if altitude_m < 0 or planet_radius_m <= 0:
            raise ValueError("invalid altitude or planet radius")
        return self.surface_g * (planet_radius_m / (planet_radius_m + altitude_m)) ** 2


@dataclass(slots=True)
class PlanetCell:
    cell_id: str
    terrain: Terrain
    x: float = 0.0
    y: float = 0.0
    elevation_m: float = 0.0
    atmosphere: Atmosphere = field(default_factory=Atmosphere)
    ocean: OceanWater | None = None
    tree_cover: float = 0.0
    factory_emissions: float = 0.0
    wild_animal_pressure: float = 0.0

    def __post_init__(self) -> None:
        if not self.cell_id.strip():
            raise ValueError("cell_id cannot be empty")
        if not 0.0 <= self.tree_cover <= 1.0 or self.factory_emissions < 0 or not 0.0 <= self.wild_animal_pressure <= 1.0:
            raise ValueError("invalid cell ecological values")
        if self.terrain == Terrain.OCEAN and self.ocean is None:
            self.ocean = OceanWater()

    @property
    def environment_type(self) -> EnvironmentType:
        return EnvironmentType.OCEAN if self.terrain == Terrain.OCEAN else EnvironmentType.LAND

    @property
    def human_can_breathe(self) -> bool:
        return self.environment_type == EnvironmentType.LAND and self.atmosphere.breathable_for_humans

    @property
    def human_wildlife_risk(self) -> float:
        return self.wild_animal_pressure * (1.0 + self.tree_cover)

    def apply_factory_emissions(self, emission: float) -> None:
        if emission < 0:
            raise ValueError("emission cannot be negative")
        self.factory_emissions += emission
        self.atmosphere.pollutants_index += emission
        self.atmosphere.carbon_dioxide_ppm += emission * 10.0
        self.atmosphere.oxygen_fraction = max(0.01, self.atmosphere.oxygen_fraction - emission * 0.00001)

    def apply_tree_exchange(self, tree_cover_delta: float, sunlight_factor: float = 1.0) -> None:
        if not -1.0 <= tree_cover_delta <= 1.0 or sunlight_factor < 0:
            raise ValueError("invalid tree exchange parameters")
        self.tree_cover = max(0.0, min(1.0, self.tree_cover + tree_cover_delta))
        oxygen_recovery = self.tree_cover * sunlight_factor * 0.00001
        self.atmosphere.oxygen_fraction = min(0.30, self.atmosphere.oxygen_fraction + oxygen_recovery)
        self.atmosphere.carbon_dioxide_ppm = max(0.0, self.atmosphere.carbon_dioxide_ppm - oxygen_recovery * 1_000_000.0)


@dataclass(slots=True)
class Planet:
    """Large-world container for land, oceans, atmosphere, gravity and space."""

    name: str = "Genesis"
    radius_m: float = 6_371_000.0
    gravity: GravityField = field(default_factory=GravityField)
    cells: dict[str, PlanetCell] = field(default_factory=dict)

    def add_cell(self, cell: PlanetCell) -> None:
        if cell.cell_id in self.cells:
            raise ValueError(f"planet cell already exists: {cell.cell_id}")
        self.cells[cell.cell_id] = cell

    def cell(self, cell_id: str) -> PlanetCell:
        try:
            return self.cells[cell_id]
        except KeyError as exc:
            raise KeyError(f"unknown planet cell: {cell_id}") from exc


@dataclass(frozen=True, slots=True)
class SpaceEnvironment:
    """Vacuum environment: no breathable atmosphere and no liquid-water habitat."""

    pressure_kpa: float = 0.0
    oxygen_fraction: float = 0.0
    temperature_c: float = -270.0

    @property
    def human_can_breathe(self) -> bool:
        return False

    @property
    def fish_can_live(self) -> bool:
        return False
