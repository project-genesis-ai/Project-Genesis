from __future__ import annotations

from dataclasses import dataclass

from genesis.life.animal import Animal
from genesis.life.migration import HabitatConditions, MigrationProfile, decide_migration
from genesis.life.organism import Organism


@dataclass(frozen=True, slots=True)
class MigrationRecord:
    organism_id: str
    source: tuple[int, int]
    destination: tuple[int, int]
    reason: str
    urgency: float


class AnimalMigrationRuntime:
    """Applies environment-driven migration decisions to mobile organisms."""

    def evaluate(
        self,
        organism: Organism,
        profile: MigrationProfile,
        current: HabitatConditions,
        candidates: dict[str, tuple[HabitatConditions, float, tuple[int, int]]],
    ) -> MigrationRecord | None:
        decision_candidates = {
            key: (conditions, distance) for key, (conditions, distance, _) in candidates.items()
        }
        decision = decide_migration(profile, current, decision_candidates)
        if not decision.should_migrate or decision.destination_id is None:
            return None
        target = candidates[decision.destination_id][2]
        source = (round(organism.position.x), round(organism.position.z))
        urgency = min(1.0, max(0.0, decision.suitability_destination - decision.suitability_current))
        return MigrationRecord(organism.organism_id, source, target, decision.reason, urgency)


class DomesticationCoupler:
    """Connects repeated human contact to animal domestication traits."""

    def apply_interaction(self, animal: Animal, positive: bool) -> None:
        animal.encounter_human(positive_interaction=positive)
