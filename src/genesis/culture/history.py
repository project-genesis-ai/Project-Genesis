from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class HistoricalEvent:
    tick: int
    kind: str
    description: str
    actors: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.tick < 0 or not self.kind.strip() or not self.description.strip():
            raise ValueError("invalid historical event")


@dataclass(slots=True)
class CulturalMemory:
    events: list[HistoricalEvent] = field(default_factory=list)
    traditions: dict[str, int] = field(default_factory=dict)

    def record(self, event: HistoricalEvent) -> None:
        self.events.append(event)

    def teach_tradition(self, name: str, tick: int = 0) -> None:
        if not name.strip() or tick < 0:
            raise ValueError("tradition name and non-negative tick are required")
        self.traditions[name] = tick

    def recent(self, limit: int = 10) -> tuple[HistoricalEvent, ...]:
        if limit < 0:
            raise ValueError("limit cannot be negative")
        return tuple(self.events[-limit:]) if limit else ()
