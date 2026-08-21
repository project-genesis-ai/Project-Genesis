from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RegionWork:
    region_id: int
    population: int
    detail: str
    lod: int = 0


@dataclass(slots=True)
class PopulationScaler:
    """Deterministic population partitioning and level-of-detail planning.

    Scaling is a scheduling plan only: it never changes canonical simulation state
    or the semantics of an individual agent/organism update.
    """

    region_capacity: int = 100_000
    hybrid_threshold: int = 100_000
    aggregate_threshold: int = 1_000_000

    def __post_init__(self) -> None:
        if self.region_capacity <= 0:
            raise ValueError("region_capacity must be positive")
        if self.hybrid_threshold <= 0 or self.aggregate_threshold <= self.hybrid_threshold:
            raise ValueError("invalid LOD thresholds")

    def detail_for(self, population: int) -> tuple[str, int]:
        if population < 0:
            raise ValueError("population cannot be negative")
        if population < self.hybrid_threshold:
            return "individual", 0
        if population < self.aggregate_threshold:
            return "hybrid", 1
        return "aggregate", 2

    def partition(self, population: int) -> tuple[RegionWork, ...]:
        if population < 0:
            raise ValueError("population cannot be negative")
        if population == 0:
            return ()
        detail, lod = self.detail_for(population)
        regions = (population + self.region_capacity - 1) // self.region_capacity
        result: list[RegionWork] = []
        remaining = population
        for region_id in range(regions):
            size = min(self.region_capacity, remaining)
            result.append(RegionWork(region_id, size, detail, lod))
            remaining -= size
        return tuple(result)
