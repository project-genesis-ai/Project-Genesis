from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .genetics import Genome
from .migration import MigrationProfile


class TrophicLevel(StrEnum):
    PRODUCER = "producer"
    HERBIVORE = "herbivore"
    CARNIVORE = "carnivore"
    OMNIVORE = "omnivore"
    DECOMPOSER = "decomposer"


@dataclass(frozen=True, slots=True)
class Species:
    """Species-level ecological and biological constraints."""

    species_id: str
    common_name: str
    trophic_level: TrophicLevel
    mature_age_ticks: int
    max_age_ticks: int
    reproduction_probability: float
    movement_speed_mps: float
    food_species: tuple[str, ...] = ()
    carrying_capacity: int = 100
    reference_genome: Genome = Genome()
    migration_profile: MigrationProfile | None = None

    def __post_init__(self) -> None:
        if not self.species_id.strip() or not self.common_name.strip():
            raise ValueError("Species identifiers and names cannot be empty")
        if not 0 <= self.mature_age_ticks < self.max_age_ticks:
            raise ValueError("mature_age_ticks must be below max_age_ticks")
        if not 0.0 <= self.reproduction_probability <= 1.0:
            raise ValueError("reproduction_probability must be between 0 and 1")
        if self.movement_speed_mps < 0.0:
            raise ValueError("movement_speed_mps cannot be negative")
        if self.carrying_capacity <= 0:
            raise ValueError("carrying_capacity must be positive")
        if self.migration_profile is not None and self.migration_profile.species_id != self.species_id:
            raise ValueError("migration profile species_id must match species_id")
