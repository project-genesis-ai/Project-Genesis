from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Habitat(StrEnum):
    RAINFOREST = "rainforest"
    RIVER = "river"
    LAKE = "lake"
    WETLAND = "wetland"
    ISLAND = "island"
    OCEAN = "ocean"
    CAVE = "cave"
    MOUNTAIN = "mountain"
    PLAINS = "plains"


@dataclass(frozen=True, slots=True)
class WildernessScale:
    """Scale is explicit so exploration is limited by population and logistics."""

    area_km2: float
    reference_area_km2: float = 6_000_000.0

    def __post_init__(self) -> None:
        if self.area_km2 <= 0 or self.reference_area_km2 <= 0:
            raise ValueError("areas must be positive")

    @property
    def reference_multiple(self) -> float:
        return self.area_km2 / self.reference_area_km2


@dataclass(slots=True)
class FrontierRegion:
    region_id: str
    habitat: Habitat
    area_km2: float
    remoteness: float = 1.0
    human_presence: float = 0.0
    surveyed_fraction: float = 0.0
    biodiversity_index: float = 1.0
    unknown_species_index: float = 0.0
    danger_index: float = 0.0
    connected_regions: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.region_id.strip() or self.area_km2 <= 0:
            raise ValueError("invalid frontier region")
        for value, name in (
            (self.remoteness, "remoteness"),
            (self.human_presence, "human_presence"),
            (self.surveyed_fraction, "surveyed_fraction"),
            (self.biodiversity_index, "biodiversity_index"),
            (self.unknown_species_index, "unknown_species_index"),
            (self.danger_index, "danger_index"),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")

    @property
    def unexplored_fraction(self) -> float:
        return 1.0 - self.surveyed_fraction

    @property
    def discovery_probability(self) -> float:
        """Potential for novel observations, not a claim of literal cryptids."""
        return min(1.0, self.unexplored_fraction * self.biodiversity_index * (0.5 + self.remoteness))

    def explore(self, expedition_effort: float, infrastructure_access: float = 0.0) -> float:
        if expedition_effort < 0 or not 0.0 <= infrastructure_access <= 1.0:
            raise ValueError("invalid exploration parameters")
        effective = expedition_effort * (1.0 + infrastructure_access) / (1.0 + 4.0 * self.remoteness)
        delta = min(self.unexplored_fraction, effective)
        self.surveyed_fraction += delta
        self.human_presence = min(1.0, self.human_presence + delta * 0.1)
        self.remoteness = max(0.0, self.remoteness - delta * 0.2)
        return delta


@dataclass(slots=True)
class WildernessNetwork:
    scale: WildernessScale
    regions: dict[str, FrontierRegion] = field(default_factory=dict)

    def add_region(self, region: FrontierRegion) -> None:
        if region.region_id in self.regions:
            raise ValueError(f"region already exists: {region.region_id}")
        self.regions[region.region_id] = region

    def connect(self, a: str, b: str) -> None:
        if a not in self.regions or b not in self.regions:
            raise KeyError("both regions must exist")
        if a == b:
            raise ValueError("a region cannot connect to itself")
        self.regions[a].connected_regions.add(b)
        self.regions[b].connected_regions.add(a)

    @property
    def unexplored_area_km2(self) -> float:
        return sum(r.area_km2 * r.unexplored_fraction for r in self.regions.values())

    @property
    def human_accessible_area_km2(self) -> float:
        return sum(r.area_km2 * r.human_presence for r in self.regions.values())
