from __future__ import annotations

from dataclasses import dataclass
import random

from genesis.physics.vectors import Vec3

from .habitat import HabitatMap
from .organism import Organism


@dataclass(frozen=True, slots=True)
class BehaviorResult:
    action: str
    target_id: str | None = None
    resource: float = 0.0


class EcologicalBehavior:
    """Deterministic local behavior for movement, feeding, and reproduction."""

    def __init__(self, seed: int = 0) -> None:
        self._rng = random.Random(seed)

    def forage(self, organism: Organism, habitat: HabitatMap) -> BehaviorResult:
        cell = habitat.get(round(organism.position.x), round(organism.position.y))
        if cell is None:
            return BehaviorResult("wander")
        if organism.species.trophic_level.value in {"herbivore", "omnivore"}:
            gained = cell.consume_vegetation(min(0.1, organism.species.movement_speed_mps * 0.01 + 0.01))
            if gained > 0.0:
                organism.energy = min(1.0, organism.energy + gained)
                return BehaviorResult("graze", resource=gained)
        if cell.water > 0.0:
            gained = cell.consume_water(0.05)
            organism.energy = min(1.0, organism.energy + gained * 0.25)
            return BehaviorResult("drink", resource=gained)
        return BehaviorResult("wander")

    def move_toward(self, organism: Organism, target: Vec3, seconds: float = 1.0) -> BehaviorResult:
        if seconds < 0.0:
            raise ValueError("seconds cannot be negative")
        delta = target - organism.position
        distance = delta.magnitude()
        if distance == 0.0:
            return BehaviorResult("stay")
        travel = min(distance, organism.species.movement_speed_mps * seconds)
        organism.position = organism.position + delta.normalized() * travel
        return BehaviorResult("move")

    def should_reproduce(self, organism: Organism) -> bool:
        return (
            organism.alive
            and organism.age_ticks >= organism.species.mature_age_ticks
            and organism.energy >= 0.7
            and self._rng.random() < organism.species.reproduction_probability
        )
