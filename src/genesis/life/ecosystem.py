from __future__ import annotations

from dataclasses import dataclass, field

from .organism import Organism
from .species import Species, TrophicLevel


@dataclass(slots=True)
class Ecosystem:
    """Deterministic population container with simple trophic interactions."""

    species: dict[str, Species] = field(default_factory=dict)
    organisms: dict[str, Organism] = field(default_factory=dict)

    def register_species(self, species: Species) -> None:
        if species.species_id in self.species:
            raise ValueError(f"Species already registered: {species.species_id}")
        self.species[species.species_id] = species

    def add_organism(self, organism: Organism) -> None:
        if organism.species.species_id not in self.species:
            raise ValueError("Organism species must be registered first")
        if organism.organism_id in self.organisms:
            raise ValueError(f"Organism already exists: {organism.organism_id}")
        self.organisms[organism.organism_id] = organism

    def population(self, species_id: str) -> int:
        return sum(
            1 for organism in self.organisms.values()
            if organism.alive and organism.species.species_id == species_id
        )

    def available_prey(self, predator: Organism) -> tuple[Organism, ...]:
        if predator.species.trophic_level == TrophicLevel.PRODUCER:
            return ()
        allowed = set(predator.species.food_species)
        return tuple(
            organism
            for organism in self.organisms.values()
            if organism.alive
            and organism.organism_id != predator.organism_id
            and organism.species.species_id in allowed
        )

    def step(self, ticks: int = 1) -> None:
        if ticks < 0:
            raise ValueError("ticks cannot be negative")
        for organism in tuple(self.organisms.values()):
            organism.age(ticks)
            if organism.alive:
                organism.consume_energy(0.001 * ticks)
