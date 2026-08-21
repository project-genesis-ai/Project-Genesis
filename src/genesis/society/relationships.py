from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Relationship:
    a: str
    b: str
    trust: float = 0.5
    affection: float = 0.0
    respect: float = 0.0
    fear: float = 0.0

    def adjust(self, *, trust: float = 0.0, affection: float = 0.0, respect: float = 0.0, fear: float = 0.0) -> None:
        self.trust = max(-1.0, min(1.0, self.trust + trust))
        self.affection = max(-1.0, min(1.0, self.affection + affection))
        self.respect = max(-1.0, min(1.0, self.respect + respect))
        self.fear = max(0.0, min(1.0, self.fear + fear))


@dataclass(slots=True)
class RelationshipStore:
    relationships: dict[tuple[str, str], Relationship] = field(default_factory=dict)

    def get_or_create(self, a: str, b: str) -> Relationship:
        if a == b:
            raise ValueError("an agent cannot have a relationship with itself")
        key = tuple(sorted((a, b)))
        relationship = self.relationships.get(key)
        if relationship is None:
            relationship = Relationship(*key)
            self.relationships[key] = relationship
        return relationship
