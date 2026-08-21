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
    """Deterministic, resumable engineering gate model.

    The loop records evidence instead of treating a boolean as proof. Human approval
    is conditional: ordinary low-risk work can proceed from CI to ship, while high-
    impact work explicitly requires the HUMAN_GATE stage.
    """

    completed: list[EngineeringStage] | None = None
    evidence: dict[EngineeringStage, tuple[str, ...]] | None = None
    human_gate_required: bool = False
    max_evidence_items: int = 32

    def __post_init__(self) -> None:
        if self.completed is None:
            self.completed = []
        if self.evidence is None:
            self.evidence = {}
        if self.max_evidence_items < 1:
            raise ValueError("max_evidence_items must be positive")
        self._validate_state()

    def _validate_state(self) -> None:
        assert self.completed is not None
        assert self.evidence is not None
        if len(self.completed) != len(set(self.completed)):
            raise ValueError("duplicate engineering stages are not allowed")
        if any(stage not in EngineeringStage for stage in self.completed):
            raise ValueError("unknown engineering stage")

    def _previous(self, stage: EngineeringStage) -> EngineeringStage | None:
        if stage is EngineeringStage.HUMAN_GATE and not self.human_gate_required:
            return EngineeringStage.CI_GATE
        order = list(EngineeringStage)
        index = order.index(stage)
        if index == 0:
            return None
        previous = order[index - 1]
        if previous is EngineeringStage.HUMAN_GATE and not self.human_gate_required:
            return EngineeringStage.CI_GATE
        return previous

    def can_enter(self, stage: EngineeringStage) -> bool:
        if stage is EngineeringStage.HUMAN_GATE and not self.human_gate_required:
            return False
        previous = self._previous(stage)
        return previous is None or previous in self.completed

    def record(self, result: StageResult) -> None:
        if not result.passed:
            raise ValueError(f"engineering stage failed: {result.stage}")
        if not self.can_enter(result.stage):
            raise ValueError(f"stage dependency not satisfied: {result.stage}")
        assert self.completed is not None
        assert self.evidence is not None
        if result.stage in self.completed:
            return
        evidence = tuple(dict.fromkeys(item.strip() for item in result.evidence if item.strip()))
        self.completed.append(result.stage)
        self.evidence[result.stage] = evidence[: self.max_evidence_items]

    def resume(self, completed: tuple[StageResult, ...]) -> None:
        """Replay a previously persisted successful prefix deterministically."""
        for result in completed:
            self.record(result)

    def invalidate_from(self, stage: EngineeringStage) -> None:
        """Drop a stage and every dependent stage so work can be safely resumed."""
        assert self.completed is not None
        assert self.evidence is not None
        order = list(EngineeringStage)
        index = order.index(stage)
        keep = set(order[:index])
        self.completed[:] = [item for item in self.completed if item in keep]
        self.evidence = {item: values for item, values in self.evidence.items() if item in keep}

    @property
    def ready_to_ship(self) -> bool:
        assert self.completed is not None
        return EngineeringStage.SHIP in self.completed

    def pending(self) -> tuple[EngineeringStage, ...]:
        assert self.completed is not None
        return tuple(stage for stage in EngineeringStage if stage not in self.completed and (stage is not EngineeringStage.HUMAN_GATE or self.human_gate_required))

    def required_stage(self) -> EngineeringStage | None:
        pending = self.pending()
        return pending[0] if pending else None
