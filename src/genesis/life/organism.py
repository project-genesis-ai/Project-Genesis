from __future__ import annotations

from dataclasses import dataclass, field

from genesis.physics.vectors import Vec3

from .species import Species


@dataclass(slots=True)
class Organism:
    """Individual living organism with energy, health, age, and location."""

    organism_id: str
    species: Species
    position: Vec3 = Vec3()
    age_ticks: int = 0
    energy: float = 1.0
    health: float = 1.0
    alive: bool = True
    memory: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.organism_id.strip():
            raise ValueError("organism_id cannot be empty")
        if self.age_ticks < 0:
            raise ValueError("age_ticks cannot be negative")
        if not 0.0 <= self.energy <= 1.0 or not 0.0 <= self.health <= 1.0:
            raise ValueError("energy and health must be between 0 and 1")

    def age(self, ticks: int = 1) -> None:
        if ticks < 0:
            raise ValueError("Age cannot move backwards")
        if not self.alive:
            return
        self.age_ticks += ticks
        if self.age_ticks >= self.species.max_age_ticks:
            self.die()

    def consume_energy(self, amount: float) -> None:
        if amount < 0.0:
            raise ValueError("Energy consumption cannot be negative")
        self.energy = max(0.0, self.energy - amount)
        if self.energy == 0.0:
            self.health = max(0.0, self.health - amount)
        if self.health == 0.0:
            self.die()

    def die(self) -> None:
        self.alive = False
