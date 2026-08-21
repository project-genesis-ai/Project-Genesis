from __future__ import annotations

from dataclasses import dataclass, field
import random

from .ecosystem import Ecosystem
from .organism import Organism


@dataclass(slots=True)
class PopulationDynamics:
    """Applies carrying capacity, selection pressure, and optional reproduction."""

    seed: int = 0
    energy_cost_per_tick: float = 0.001
    crowding_mortality: float = 0.02
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.energy_cost_per_tick < 0.0 or self.crowding_mortality < 0.0:
            raise ValueError("population rates cannot be negative")
        self._rng = random.Random(self.seed)

    def step(self, ecosystem: Ecosystem, ticks: int = 1, reproduce: bool = True) -> tuple[Organism, ...]:
        if ticks < 0:
            raise ValueError("ticks cannot be negative")
        newborns: list[Organism] = []
        by_species: dict[str, list[Organism]] = {species_id: [] for species_id in ecosystem.species}
        for organism in ecosystem.organisms.values():
            if organism.alive:
                by_species.setdefault(organism.species.species_id, []).append(organism)

        for species in ecosystem.species.values():
            members = by_species.get(species.species_id, [])
            if len(members) > species.carrying_capacity:
                excess = len(members) - species.carrying_capacity
                candidates = sorted(members, key=lambda organism: (organism.genome.fitness if organism.genome is not None else 0.0, organism.energy, organism.age_ticks, organism.organism_id))
                for organism in candidates[:excess]:
                    organism.die()
                members = candidates[excess:]
            if not reproduce:
                continue
            breeders = [o for o in members if o.alive and o.age_ticks >= species.mature_age_ticks and o.energy >= 0.2]
            breeders.sort(key=lambda organism: organism.organism_id)
            index = 0
            while index < len(breeders):
                if len(members) + len(newborns) >= species.carrying_capacity:
                    break
                first = breeders[index]
                second = breeders[index + 1] if index + 1 < len(breeders) else first
                child_id = f"{species.species_id}-{len(ecosystem.organisms) + len(newborns) + 1}"
                child = first.reproduce(second, child_id, self._rng)
                if child is not None:
                    newborns.append(child)
                index += 2
        for newborn in newborns:
            ecosystem.add_organism(newborn)
        return tuple(newborns)
