from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RegionWork:
    region_id: int
    population: int
    detail: str


@dataclass(slots=True)
class PopulationScaler:
    """Deterministic spatial work partitioning for large populations."""

    region_capacity: int = 100_000

    def __post_init__(self) -> None:
        if self.region_capacity <= 0:
            raise ValueError("region_capacity must be positive")

    def partition(self, population: int) -> tuple[RegionWork, ...]:
        if population < 0:
            raise ValueError("population cannot be negative")
        if population == 0:
            return ()
        regions = (population + self.region_capacity - 1) // self.region_capacity
        result = []
        remaining = population
        for region_id in range(regions):
            size = min(self.region_capacity, remaining)
            result.append(RegionWork(region_id, size, "individual"))
            remaining -= size
        return tuple(result)
