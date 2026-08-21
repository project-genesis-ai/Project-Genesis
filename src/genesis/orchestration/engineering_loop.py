from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class EngineeringStage(StrEnum):
    RESEARCH = "research"
    ARCHITECTURE = "architecture"
    IMPLEMENTATION = "implementation"
    INTEGRATION = "integration"
    TESTING = "testing"
    DEBUGGING = "debugging"
    REVIEW = "review"
    CI_GATE = "ci_gate"
    HUMAN_GATE = "human_gate"
    SHIP = "ship"


@dataclass(frozen=True, slots=True)
class StageResult:
    stage: EngineeringStage
    passed: bool
    evidence: tuple[str, ...] = ()


@dataclass(slots=True)
class EngineeringLoop:
    """Deterministic in-process gate model for autonomous engineering workflows."""

    completed: list[EngineeringStage] | None = None

    def __post_init__(self) -> None:
        if self.completed is None:
            self.completed = []

    def can_enter(self, stage: EngineeringStage) -> bool:
        order = list(EngineeringStage)
        index = order.index(stage)
        return index == 0 or order[index - 1] in self.completed

    def record(self, result: StageResult) -> None:
        if not result.passed:
            raise ValueError(f"engineering stage failed: {result.stage}")
        if not self.can_enter(result.stage):
            raise ValueError(f"stage dependency not satisfied: {result.stage}")
        if result.stage not in self.completed:
            self.completed.append(result.stage)

    @property
    def ready_to_ship(self) -> bool:
        return EngineeringStage.SHIP in self.completed

    def pending(self) -> tuple[EngineeringStage, ...]:
        return tuple(stage for stage in EngineeringStage if stage not in self.completed)
