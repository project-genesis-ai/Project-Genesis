from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AnimalStatus(StrEnum):
    WILD = "wild"
    DOMESTIC = "domestic"
    STRAY = "stray"


class AnimalScale(StrEnum):
    MICRO = "micro"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    MEGAFAUNA = "megafauna"


@dataclass(frozen=True, slots=True)
class AnimalEcology:
    """Behavioral constraints shared by wild, domestic and stray animals."""

    species_id: str
    status: AnimalStatus = AnimalStatus.WILD
    scale: AnimalScale = AnimalScale.MEDIUM
    human_fear: float = 0.5
    human_trust: float = 0.0
    aggression: float = 0.2
    domestication: float = 0.0
    sociality: float = 0.5
    habitat_range_km2: float = 1.0

    def __post_init__(self) -> None:
        for value in (self.human_fear, self.human_trust, self.aggression, self.domestication, self.sociality):
            if not 0.0 <= value <= 1.0:
                raise ValueError("behavioral traits must be between 0 and 1")
        if self.habitat_range_km2 <= 0.0:
            raise ValueError("habitat range must be positive")
        if self.status == AnimalStatus.DOMESTIC and self.domestication <= 0.0:
            raise ValueError("domestic animals require domestication pressure")


@dataclass(slots=True)
class Animal:
    """Individual animal state; status can change through human/environmental interaction."""

    animal_id: str
    ecology: AnimalEcology
    age_ticks: int = 0
    health: float = 1.0
    hunger: float = 0.0
    fear: float = 0.0
    bonded_to_human: bool = False

    def __post_init__(self) -> None:
        if not self.animal_id.strip():
            raise ValueError("animal_id cannot be empty")
        if self.age_ticks < 0 or not 0.0 <= self.health <= 1.0 or not 0.0 <= self.hunger <= 1.0 or not 0.0 <= self.fear <= 1.0:
            raise ValueError("invalid animal physiological state")

    @property
    def danger_to_human(self) -> float:
        base = self.ecology.aggression * (1.0 - self.ecology.human_trust)
        if self.ecology.status == AnimalStatus.WILD:
            return min(1.0, base * (1.0 + self.ecology.human_fear))
        if self.ecology.status == AnimalStatus.STRAY:
            return min(1.0, base * 1.1)
        return min(1.0, base * 0.5)

    def encounter_human(self, positive_interaction: bool = False) -> None:
        if positive_interaction:
            self.ecology = AnimalEcology(
                **{**self.ecology.__dict__, "human_fear": max(0.0, self.ecology.human_fear - 0.05), "human_trust": min(1.0, self.ecology.human_trust + 0.05)}
            )
            self.bonded_to_human = True
        else:
            self.fear = min(1.0, self.fear + 0.2)


@dataclass(slots=True)
class AnimalPopulation:
    animals: dict[str, Animal]

    def by_status(self, status: AnimalStatus) -> list[Animal]:
        return [animal for animal in self.animals.values() if animal.ecology.status == status]

    def danger_index(self) -> float:
        if not self.animals:
            return 0.0
        return sum(animal.danger_to_human for animal in self.animals.values()) / len(self.animals)
