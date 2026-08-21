from __future__ import annotations

from dataclasses import dataclass, field

from .needs import Needs
from .personality import Personality


@dataclass(slots=True)
class Agent:
    """Minimal autonomous citizen state owned by the simulation."""

    agent_id: str
    name: str
    age_ticks: int = 0
    health: float = 1.0
    needs: Needs = field(default_factory=Needs)
    personality: Personality = field(default_factory=Personality)
    inventory: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.agent_id.strip():
            raise ValueError("agent_id cannot be empty")
        if not self.name.strip():
            raise ValueError("name cannot be empty")
        if self.age_ticks < 0:
            raise ValueError("age_ticks cannot be negative")
        if not 0.0 <= self.health <= 1.0:
            raise ValueError("health must be between 0 and 1")

    def advance_age(self, ticks: int = 1) -> None:
        if ticks < 0:
            raise ValueError("Age cannot move backwards")
        self.age_ticks += ticks
