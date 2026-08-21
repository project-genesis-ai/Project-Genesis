from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RelationType(str, Enum):
    PARENT = "parent"
    CHILD = "child"
    SIBLING = "sibling"
    PARTNER = "partner"
    FRIEND = "friend"
    RIVAL = "rival"
    HOUSEHOLD = "household"


@dataclass(slots=True)
class Relationship:
    source_id: str
    target_id: str
    relation: RelationType
    trust: float = 0.5
    affinity: float = 0.0
    interaction_count: int = 0

    def __post_init__(self) -> None:
        if not self.source_id.strip() or not self.target_id.strip():
            raise ValueError("relationship ids cannot be empty")
        if self.source_id == self.target_id:
            raise ValueError("self relationships are not allowed")
        if not 0.0 <= self.trust <= 1.0:
            raise ValueError("trust must be between 0 and 1")
        if not -1.0 <= self.affinity <= 1.0:
            raise ValueError("affinity must be between -1 and 1")
        if self.interaction_count < 0:
            raise ValueError("interaction_count cannot be negative")

    def interact(self, *, positive: float = 0.0, negative: float = 0.0) -> None:
        if positive < 0.0 or negative < 0.0:
            raise ValueError("interaction effects cannot be negative")
        self.interaction_count += 1
        self.trust = max(0.0, min(1.0, self.trust + positive * 0.1 - negative * 0.15))
        self.affinity = max(-1.0, min(1.0, self.affinity + positive * 0.1 - negative * 0.1))


@dataclass(slots=True)
class RelationshipGraph:
    relationships: dict[tuple[str, str, RelationType], Relationship] = field(default_factory=dict)

    def connect(self, relationship: Relationship) -> None:
        key = (relationship.source_id, relationship.target_id, relationship.relation)
        self.relationships[key] = relationship

    def get(self, source_id: str, target_id: str, relation: RelationType) -> Relationship | None:
        return self.relationships.get((source_id, target_id, relation))

    def neighbors(self, source_id: str) -> tuple[Relationship, ...]:
        return tuple(r for r in self.relationships.values() if r.source_id == source_id)

    def trust(self, source_id: str, target_id: str) -> float:
        matches = [r.trust for r in self.neighbors(source_id) if r.target_id == target_id]
        return max(matches, default=0.5)
