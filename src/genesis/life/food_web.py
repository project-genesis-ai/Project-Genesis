from __future__ import annotations

from dataclasses import dataclass

from .ecosystem import Ecosystem
from .organism import Organism
from .species import TrophicLevel


@dataclass(frozen=True, slots=True)
class FeedingResult:
    predator_id: str
    prey_id: str
    energy_transferred: float


class FoodWeb:
    """Deterministic trophic interactions with explicit energy transfer."""

    def __init__(self, energy_transfer_efficiency: float = 0.2) -> None:
        if not 0.0 <= energy_transfer_efficiency <= 1.0:
            raise ValueError("energy_transfer_efficiency must be between 0 and 1")
        self.energy_transfer_efficiency = energy_transfer_efficiency

    def feed(self, predator: Organism, prey: Organism) -> FeedingResult | None:
        if not predator.alive or not prey.alive or predator.organism_id == prey.organism_id:
            return None
        if prey.species.species_id not in predator.species.food_species:
            return None
        prey_energy = prey.energy
        prey.die()
        gained = prey_energy * self.energy_transfer_efficiency
        predator.energy = min(1.0, predator.energy + gained)
        return FeedingResult(predator.organism_id, prey.organism_id, gained)

    def best_prey(self, ecosystem: Ecosystem, predator: Organism) -> Organism | None:
        candidates = ecosystem.available_prey(predator)
        if not candidates or predator.species.trophic_level == TrophicLevel.PRODUCER:
            return None
        return max(candidates, key=lambda organism: (organism.energy, -organism.age_ticks, organism.organism_id))
