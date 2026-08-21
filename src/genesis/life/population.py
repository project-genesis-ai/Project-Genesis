from __future__ import annotations

from dataclasses import dataclass, field
import random

from genesis.physics.vectors import Vec3

from .ecosystem import Ecosystem
from .organism import Organism


@dataclass(slots=True)
class PopulationDynamics:
    """Applies carrying capacity, optional legacy reproduction, and mortality."""

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
        for species in ecosystem.species.values():
            members = [o for o in ecosystem.organisms.values() if o.alive and o.species.species_id == species.species_id]
            if len(members) > species.carrying_capacity:
                excess = len(members) - species.carrying_capacity
                candidates = sorted(members, key=lambda organism: (organism.energy, organism.age_ticks, organism.organism_id))
                for organism in candidates[:excess]:
                    organism.die()
                members = candidates[excess:]
            if not reproduce:
                continue
            breeders = [o for o in members if o.alive and o.age_ticks >= species.mature_age_ticks and o.energy >= 0.7]
            for parent in breeders:
                if len(members) + len(newborns) >= species.carrying_capacity:
                    break
                probability = min(1.0, species.reproduction_probability * ticks)
                if self._rng.random() >= probability:
                    continue
                child_id = f"{species.species_id}-{len(ecosystem.organisms) + len(newborns) + 1}"
                parent.energy = max(0.0, parent.energy - 0.2)
                newborns.append(Organism(child_id, species, position=Vec3(parent.position.x, parent.position.y, parent.position.z)))
        for newborn in newborns:
            ecosystem.add_organism(newborn)
        return tuple(newborns)
