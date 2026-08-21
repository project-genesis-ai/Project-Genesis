from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class KnowledgeStatus(StrEnum):
    PROVISIONAL = "provisional"
    VERIFIED = "verified"
    DISPUTED = "disputed"


@dataclass(frozen=True, slots=True)
class Experience:
    experience_id: str
    domain: str
    actor_id: str
    tick: int
    observation: str
    action: str
    outcome: str
    success: bool
    confidence: float = 0.5

    def __post_init__(self) -> None:
        if not self.experience_id.strip() or not self.domain.strip() or not self.actor_id.strip():
            raise ValueError("experience identity fields cannot be empty")
        if self.tick < 0:
            raise ValueError("experience tick cannot be negative")
        if not self.observation.strip() or not self.action.strip() or not self.outcome.strip():
            raise ValueError("experience text cannot be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("experience confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class KnowledgeLesson:
    lesson_id: str
    domain: str
    statement: str
    evidence_ids: tuple[str, ...]
    confidence: float
    status: KnowledgeStatus = KnowledgeStatus.PROVISIONAL
    generation: int = 0

    def __post_init__(self) -> None:
        if not self.lesson_id.strip() or not self.domain.strip() or not self.statement.strip():
            raise ValueError("lesson identity and statement cannot be empty")
        if not self.evidence_ids or len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise ValueError("lessons require unique evidence ids")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("lesson confidence must be between 0 and 1")
        if self.generation < 0:
            raise ValueError("lesson generation cannot be negative")


@dataclass(frozen=True, slots=True)
class KnowledgeTransfer:
    learner_id: str
    lesson_id: str
    domain: str
    tick: int
    confidence: float

    def __post_init__(self) -> None:
        if not self.learner_id.strip() or not self.lesson_id.strip() or not self.domain.strip():
            raise ValueError("knowledge transfer identity fields cannot be empty")
        if self.tick < 0 or not 0.0 <= self.confidence <= 1.0:
            raise ValueError("invalid knowledge transfer")
