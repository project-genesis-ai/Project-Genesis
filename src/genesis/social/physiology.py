from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LifeStage(str, Enum):
    INFANT = "infant"
    CHILD = "child"
    ADOLESCENT = "adolescent"
    ADULT = "adult"
    ELDER = "elder"


@dataclass(slots=True)
class HumanPhysiology:
    """Deterministic human state model independent of rendering or LLMs."""

    age_ticks: int = 0
    health: float = 1.0
    nutrition: float = 1.0
    hydration: float = 1.0
    energy: float = 1.0
    sleep: float = 1.0
    injury: float = 0.0
    alive: bool = True

    def __post_init__(self) -> None:
        if self.age_ticks < 0:
            raise ValueError("age_ticks cannot be negative")
        for name in ("health", "nutrition", "hydration", "energy", "sleep"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if not 0.0 <= self.injury <= 1.0:
            raise ValueError("injury must be between 0 and 1")

    @property
    def life_stage(self) -> LifeStage:
        if self.age_ticks < 100:
            return LifeStage.INFANT
        if self.age_ticks < 500:
            return LifeStage.CHILD
        if self.age_ticks < 800:
            return LifeStage.ADOLESCENT
        if self.age_ticks < 2400:
            return LifeStage.ADULT
        return LifeStage.ELDER

    def step(self, ticks: int = 1, *, activity: float = 0.2) -> None:
        if ticks < 0:
            raise ValueError("ticks cannot be negative")
        if not 0.0 <= activity <= 1.0:
            raise ValueError("activity must be between 0 and 1")
        if not self.alive:
            return
        self.age_ticks += ticks
        demand = (0.01 + 0.02 * activity) * ticks
        self.energy = max(0.0, self.energy - demand)
        self.hydration = max(0.0, self.hydration - 0.008 * ticks)
        self.sleep = max(0.0, self.sleep - 0.006 * ticks)
        stress = max(0.0, 1.0 - min(self.nutrition, self.hydration, self.sleep))
        self.health = max(0.0, min(1.0, self.health - stress * 0.002 * ticks - self.injury * 0.001 * ticks))
        if self.age_ticks >= 3600 or self.health <= 0.0:
            self.alive = False

    def rest(self, ticks: int = 1) -> None:
        if ticks < 0:
            raise ValueError("ticks cannot be negative")
        self.sleep = min(1.0, self.sleep + 0.02 * ticks)
        self.energy = min(1.0, self.energy + 0.015 * ticks)
        self.health = min(1.0, self.health + 0.003 * ticks)

    def eat(self, nutrition: float) -> None:
        if nutrition < 0.0:
            raise ValueError("nutrition cannot be negative")
        self.nutrition = min(1.0, self.nutrition + nutrition)

    def drink(self, hydration: float) -> None:
        if hydration < 0.0:
            raise ValueError("hydration cannot be negative")
        self.hydration = min(1.0, self.hydration + hydration)

    def injure(self, severity: float) -> None:
        if not 0.0 <= severity <= 1.0:
            raise ValueError("severity must be between 0 and 1")
        self.injury = min(1.0, self.injury + severity)
        self.health = max(0.0, self.health - severity * 0.5)
        if self.health == 0.0:
            self.alive = False
