from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Innovation:
    innovation_id: str
    name: str
    inventor_id: str
    prerequisites: frozenset[str] = frozenset()
    utility: float = 0.5

    def __post_init__(self) -> None:
        if not self.innovation_id.strip() or not self.name.strip() or not self.inventor_id.strip() or not 0.0 <= self.utility <= 1.0:
            raise ValueError("invalid innovation")


@dataclass(slots=True)
class InnovationSystem:
    discovered: dict[str, Innovation] = field(default_factory=dict)
    adoption: dict[str, set[str]] = field(default_factory=dict)

    def discover(self, innovation: Innovation, known: set[str]) -> bool:
        if not innovation.prerequisites.issubset(known) or innovation.innovation_id in self.discovered:
            return False
        self.discovered[innovation.innovation_id] = innovation
        self.adoption.setdefault(innovation.innovation_id, set()).add(innovation.inventor_id)
        return True

    def adopt(self, innovation_id: str, agent_id: str) -> None:
        if innovation_id not in self.discovered:
            raise ValueError("unknown innovation")
        if not agent_id.strip():
            raise ValueError("agent_id cannot be empty")
        self.adoption.setdefault(innovation_id, set()).add(agent_id)

    def adoption_rate(self, innovation_id: str, population: int) -> float:
        if population < 1:
            raise ValueError("population must be positive")
        return min(1.0, len(self.adoption.get(innovation_id, set())) / population)
