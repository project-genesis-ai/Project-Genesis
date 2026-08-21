from __future__ import annotations

from dataclasses import dataclass, field
import math
import random

from genesis.physics.vectors import Vec3

from .genetics import Genome
from .physiology import Physiology
from .species import Species


@dataclass(slots=True)
class Organism:
    """Individual organism with explicit life, energy and inherited traits."""

    organism_id: str
    species: Species
    position: Vec3 = Vec3()
    age_ticks: int = 0
    energy: float = 1.0
    health: float = 1.0
    alive: bool = True
    memory: dict[str, float] = field(default_factory=dict)
    genome: Genome | None = None

    def __post_init__(self) -> None:
        if not self.organism_id.strip():
            raise ValueError("organism_id cannot be empty")
        if self.age_ticks < 0:
            raise ValueError("age_ticks cannot be negative")
        if not 0.0 <= self.energy <= 1.0 or not 0.0 <= self.health <= 1.0:
            raise ValueError("energy and health must be between 0 and 1")
        if self.genome is None:
            self.genome = self.species.reference_genome

    @property
    def physiology(self) -> Physiology:
        assert self.genome is not None
        return Physiology(self.genome.body_mass_kg * (1.0 + 0.15 * self.age_fraction))

    @property
    def age_fraction(self) -> float:
        return min(1.0, self.age_ticks / max(1, self.species.max_age_ticks))

    @property
    def mature(self) -> bool:
        return self.alive and self.age_ticks >= self.species.mature_age_ticks

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

    def survive(self, environmental_stress: float = 0.0) -> None:
        if environmental_stress < 0:
            raise ValueError("environmental_stress cannot be negative")
        self.health = max(0.0, self.health - environmental_stress * 0.01)
        if self.health == 0.0:
            self.die()

    def die(self) -> None:
        self.alive = False

    def reproduce(self, partner: Organism, child_id: str, rng: random.Random) -> Organism | None:
        if not self.mature or not partner.mature or partner.species.species_id != self.species.species_id:
            return None
        if self.energy < 0.2 or partner.energy < 0.2:
            return None
        assert self.genome is not None and partner.genome is not None
        fertility = math.sqrt(self.genome.fertility * partner.genome.fertility)
        probability = min(1.0, self.species.reproduction_probability * fertility)
        if rng.random() >= probability:
            return None
        self.consume_energy(0.1)
        partner.consume_energy(0.1)
        child_genome = Genome.inherit(self.genome, partner.genome, rng)
        return Organism(child_id, self.species, position=self.position, genome=child_genome)
