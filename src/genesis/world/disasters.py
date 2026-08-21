from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DisasterType(str, Enum):
    FLOOD = "flood"
    DROUGHT = "drought"
    WILDFIRE = "wildfire"
    STORM = "storm"
    EARTHQUAKE = "earthquake"


@dataclass(frozen=True, slots=True)
class Disaster:
    disaster_id: str
    kind: DisasterType
    severity: float
    duration_ticks: int
    remaining_ticks: int | None = None

    def __post_init__(self) -> None:
        if not self.disaster_id.strip() or not 0.0 <= self.severity <= 1.0 or self.duration_ticks < 1:
            raise ValueError("invalid disaster")
        if self.remaining_ticks is not None and not 0 <= self.remaining_ticks <= self.duration_ticks:
            raise ValueError("invalid remaining duration")

    @property
    def active(self) -> bool:
        return (self.duration_ticks if self.remaining_ticks is None else self.remaining_ticks) > 0


@dataclass(slots=True)
class DisasterSystem:
    active: dict[str, Disaster] = field(default_factory=dict)
    history: list[Disaster] = field(default_factory=list)

    def start(self, disaster: Disaster) -> None:
        if disaster.disaster_id in self.active:
            raise ValueError(f"disaster already active: {disaster.disaster_id}")
        self.active[disaster.disaster_id] = disaster

    def step(self, ticks: int = 1) -> tuple[Disaster, ...]:
        if ticks < 0:
            raise ValueError("ticks cannot be negative")
        ended: list[Disaster] = []
        for disaster_id, disaster in list(self.active.items()):
            remaining = (disaster.duration_ticks if disaster.remaining_ticks is None else disaster.remaining_ticks) - ticks
            if remaining <= 0:
                ended.append(disaster)
                self.history.append(disaster)
                del self.active[disaster_id]
            else:
                self.active[disaster_id] = Disaster(disaster.disaster_id, disaster.kind, disaster.severity, disaster.duration_ticks, remaining)
        return tuple(ended)
