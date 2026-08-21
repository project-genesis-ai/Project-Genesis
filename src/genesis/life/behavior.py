from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from genesis.physics.vectors import Vec3

from .habitat import HabitatMap
from .organism import Organism


@dataclass(frozen=True, slots=True)
class BehaviorResult:
    action: str
    target_id: str | None = None
    resource: float = 0.0


class EcologicalBehavior:
    """Deterministic local behavior for perception, action, and feedback.

    The organism remains the authoritative mutable state. This service only
    derives decisions and applies actions through the existing organism and
    habitat APIs; it does not create a second behavioral state owner.
    """

    def __init__(self, seed: int = 0) -> None:
        self.seed = int(seed)

    def _roll(self, organism: Organism) -> float:
        token = sha256(
            f"{self.seed}|{organism.organism_id}|{organism.age_ticks}".encode("utf-8")
        ).hexdigest()[:16]
        return int(token, 16) / 0xFFFFFFFFFFFFFFFF

    def decide(self, organism: Organism, habitat: HabitatMap) -> BehaviorResult:
        """Perceive local resources and select a bounded survival action."""
        if not organism.alive:
            return BehaviorResult("dead")

        cell = habitat.get(round(organism.position.x), round(organism.position.y))
        if cell is None:
            action = "wander"
        elif organism.health < 0.25:
            action = "rest"
        elif organism.energy < 0.3:
            action = "forage"
        elif cell.water < 0.1 and cell.vegetation <= 0.0:
            action = "wander"
        elif cell.vegetation > 0.0 or cell.water > 0.0:
            action = "forage"
        else:
            action = "rest"

        previous = organism.memory.get(action, 0.0)
        organism.memory["decision_count"] = organism.memory.get("decision_count", 0.0) + 1.0
        organism.memory["last_action_score"] = previous
        return BehaviorResult(action)

    def act(self, organism: Organism, habitat: HabitatMap) -> BehaviorResult:
        """Execute one decision and record bounded outcome feedback."""
        decision = self.decide(organism, habitat)
        if decision.action == "forage":
            result = self.forage(organism, habitat)
        elif decision.action == "wander":
            result = BehaviorResult("wander")
        elif decision.action == "rest":
            before = organism.energy
            organism.energy = min(1.0, organism.energy + 0.02)
            result = BehaviorResult("rest", resource=organism.energy - before)
        else:
            result = decision

        organism.memory[result.action] = min(
            1.0, max(-1.0, organism.memory.get(result.action, 0.0) * 0.95 + result.resource)
        )
        return result

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
        """Use a stable per-organism roll so iteration order cannot change behavior."""
        if not (
            organism.alive
            and organism.age_ticks >= organism.species.mature_age_ticks
            and organism.energy >= 0.7
        ):
            return False
        return self._roll(organism) < organism.species.reproduction_probability
