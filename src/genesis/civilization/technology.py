from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Technology:
    technology_id: str
    name: str
    prerequisites: set[str] = field(default_factory=set)
    unlocked: bool = False
    research_cost: float = 1.0
    progress: float = 0.0

    def __post_init__(self) -> None:
        if not self.technology_id.strip() or not self.name.strip() or self.research_cost <= 0:
            raise ValueError("invalid technology")
        if not 0.0 <= self.progress <= 1.0:
            raise ValueError("progress must be between 0 and 1")

    def can_unlock(self, known: set[str]) -> bool:
        return self.prerequisites.issubset(known)

    def research(self, effort: float, known: set[str]) -> bool:
        if effort < 0:
            raise ValueError("effort cannot be negative")
        if not self.can_unlock(known):
            return False
        self.progress = min(1.0, self.progress + effort / self.research_cost)
        if self.progress >= 1.0:
            self.unlocked = True
        return self.unlocked
