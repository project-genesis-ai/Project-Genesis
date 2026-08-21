from __future__ import annotations

from dataclasses import dataclass, field
import random

from .organism import Organism
from .species import Species, TrophicLevel


@dataclass(slots=True)
class Ecosystem:
    """Deterministic population container with density-dependent ecology."""

    species: dict[str, Species] = field(default_factory=dict)
    organisms: dict[str, Organism] = field(default_factory=dict)
    seed: int = 0
    _next_birth_id: int = 0
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

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
        return sum(1 for organism in self.organisms.values() if organism.alive and organism.species.species_id == species_id)

    def available_prey(self, predator: Organism) -> tuple[Organism, ...]:
        if predator.species.trophic_level == TrophicLevel.PRODUCER:
            return ()
        allowed = set(predator.species.food_species)
        return tuple(
            organism for organism in self.organisms.values()
            if organism.alive and organism.organism_id != predator.organism_id
            and organism.species.species_id in allowed
        )

    def _pair_mature(self, species_id: str) -> list[tuple[Organism, Organism]]:
        mature = [o for o in self.organisms.values() if o.alive and o.mature and o.species.species_id == species_id]
        mature.sort(key=lambda o: o.organism_id)
        return list(zip(mature[::2], mature[1::2]))

    def step(self, ticks: int = 1, environmental_stress: float = 0.0) -> None:
        if ticks < 0:
            raise ValueError("ticks cannot be negative")
        if environmental_stress < 0:
            raise ValueError("environmental_stress cannot be negative")
        for _ in range(ticks):
            for organism in tuple(self.organisms.values()):
                organism.age(1)
                if organism.alive:
                    demand = min(0.05, organism.physiology.basal_power_watts * 1e-5)
                    organism.consume_energy(demand)
                    organism.survive(environmental_stress)

            for species_id, species in self.species.items():
                population = self.population(species_id)
                if population >= species.carrying_capacity:
                    continue
                density_factor = max(0.0, 1.0 - population / species.carrying_capacity)
                for parent_a, parent_b in self._pair_mature(species_id):
                    if self._rng.random() >= density_factor:
                        continue
                    child_id = f"{species_id}:birth:{self._next_birth_id}"
                    self._next_birth_id += 1
                    child = parent_a.reproduce(parent_b, child_id, self._rng)
                    if child is not None:
                        self.organisms[child.organism_id] = child
