from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AgeStage(str, Enum):
    INFANT = "infant"
    CHILD = "child"
    ADOLESCENT = "adolescent"
    ADULT = "adult"
    ELDER = "elder"
    DECEASED = "deceased"


@dataclass(slots=True)
class HumanLifeState:
    agent_id: str
    age_ticks: int = 0
    alive: bool = True
    fertility: float = 1.0

    @property
    def stage(self) -> AgeStage:
        if not self.alive:
            return AgeStage.DECEASED
        if self.age_ticks < 10:
            return AgeStage.INFANT
        if self.age_ticks < 20:
            return AgeStage.CHILD
        if self.age_ticks < 30:
            return AgeStage.ADOLESCENT
        if self.age_ticks < 300:
            return AgeStage.ADULT
        return AgeStage.ELDER

    def advance(self, ticks: int = 1, max_age: int = 360) -> bool:
        if ticks < 0 or max_age < 1:
            raise ValueError("invalid lifecycle parameters")
        if not self.alive:
            return False
        self.age_ticks += ticks
        self.fertility = max(0.0, min(1.0, 1.0 - max(0, self.age_ticks - 40) / 200.0))
        if self.age_ticks >= max_age:
            self.alive = False
        return self.alive


@dataclass(frozen=True, slots=True)
class BirthRecord:
    birth_id: str
    parent_ids: tuple[str, ...]
    child_id: str
    tick: int

    def __post_init__(self) -> None:
        if not self.birth_id.strip() or not self.child_id.strip() or not self.parent_ids or self.tick < 0:
            raise ValueError("invalid birth record")


@dataclass(slots=True)
class DemographicSystem:
    people: dict[str, HumanLifeState] = field(default_factory=dict)
    births: list[BirthRecord] = field(default_factory=list)

    def register(self, person: HumanLifeState) -> None:
        if person.agent_id in self.people:
            raise ValueError(f"person already exists: {person.agent_id}")
        self.people[person.agent_id] = person

    def step(self, ticks: int = 1, max_age: int = 360) -> tuple[str, ...]:
        deaths: list[str] = []
        for person in self.people.values():
            was_alive = person.alive
            person.advance(ticks, max_age)
            if was_alive and not person.alive:
                deaths.append(person.agent_id)
        return tuple(deaths)

    def record_birth(self, record: BirthRecord) -> None:
        if record.child_id in self.people:
            raise ValueError(f"child already exists: {record.child_id}")
        self.births.append(record)
        self.people[record.child_id] = HumanLifeState(record.child_id)
