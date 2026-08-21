from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Institution:
    institution_id: str
    name: str
    members: set[str] = field(default_factory=set)
    rules: dict[str, float] = field(default_factory=dict)
    budget: float = 0.0

    def __post_init__(self) -> None:
        if not self.institution_id.strip() or not self.name.strip() or self.budget < 0:
            raise ValueError("invalid institution")

    def add_member(self, agent_id: str) -> None:
        if not agent_id.strip():
            raise ValueError("agent_id cannot be empty")
        self.members.add(agent_id)

    def remove_member(self, agent_id: str) -> None:
        self.members.discard(agent_id)

    def set_rule(self, name: str, strength: float = 1.0) -> None:
        if not name.strip() or not 0.0 <= strength <= 1.0:
            raise ValueError("invalid rule")
        self.rules[name] = strength

    def fund(self, amount: float) -> None:
        if amount < 0:
            raise ValueError("funding cannot be negative")
        self.budget += amount

    def spend(self, amount: float) -> bool:
        if amount < 0:
            raise ValueError("spending cannot be negative")
        if amount > self.budget:
            return False
        self.budget -= amount
        return True
