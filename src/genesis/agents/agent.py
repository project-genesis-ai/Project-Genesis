from __future__ import annotations

from dataclasses import dataclass, field

from genesis.cognition.memory import MemoryStore
from .needs import Needs
from .personality import Personality


@dataclass(slots=True)
class Agent:
    """Autonomous citizen state; cognition, society and economy attach to this identity."""

    agent_id: str
    name: str
    age_ticks: int = 0
    health: float = 1.0
    needs: Needs = field(default_factory=Needs)
    personality: Personality = field(default_factory=Personality)
    inventory: dict[str, float] = field(default_factory=dict)
    wealth: float = 0.0
    skills: dict[str, float] = field(default_factory=dict)
    knowledge: set[str] = field(default_factory=set)
    memory: MemoryStore = field(default_factory=MemoryStore)
    world_x: int = 0
    world_y: int = 0

    def __post_init__(self) -> None:
        if not self.agent_id.strip():
            raise ValueError("agent_id cannot be empty")
        if not self.name.strip():
            raise ValueError("name cannot be empty")
        if self.age_ticks < 0:
            raise ValueError("age_ticks cannot be negative")
        if not 0.0 <= self.health <= 1.0:
            raise ValueError("health must be between 0 and 1")
        if self.wealth < 0.0:
            raise ValueError("wealth cannot be negative")

    def advance_age(self, ticks: int = 1) -> None:
        if ticks < 0:
            raise ValueError("Age cannot move backwards")
        self.age_ticks += ticks

    def move_world(self, x: int, y: int) -> None:
        self.world_x = int(x)
        self.world_y = int(y)

    def learn(self, knowledge: str, confidence: float = 1.0) -> None:
        if not knowledge.strip():
            raise ValueError("knowledge cannot be empty")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        self.knowledge.add(knowledge)
