from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Goal:
    goal_id: str
    name: str
    urgency: float = 0.5

    def __post_init__(self) -> None:
        if not self.goal_id.strip() or not self.name.strip():
            raise ValueError("goal identity and name cannot be empty")
        if not 0.0 <= self.urgency <= 1.0:
            raise ValueError("urgency must be between 0 and 1")
