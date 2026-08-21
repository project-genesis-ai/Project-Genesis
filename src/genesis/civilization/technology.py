from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Technology:
    technology_id: str
    name: str
    prerequisites: set[str] = field(default_factory=set)
    unlocked: bool = False

    def can_unlock(self, known: set[str]) -> bool:
        return self.prerequisites.issubset(known)
