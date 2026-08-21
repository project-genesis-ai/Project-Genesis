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
        if len(self.actors) != len(set(self.actors)):
            raise ValueError("historical event actors must be unique")


@dataclass(slots=True)
class CulturalMemory:
    """Bounded collective history and generational traditions."""

    events: list[HistoricalEvent] = field(default_factory=list)
    traditions: dict[str, int] = field(default_factory=dict)
    capacity: int = 2048

    def __post_init__(self) -> None:
        if self.capacity < 1:
            raise ValueError("cultural memory capacity must be positive")
        if len(self.events) > self.capacity:
            self.events[:] = self.events[-self.capacity :]

    def record(self, event: HistoricalEvent) -> None:
        self.events.append(event)
        if len(self.events) > self.capacity:
            del self.events[: len(self.events) - self.capacity]

    def teach_tradition(self, name: str, tick: int = 0) -> None:
        if not name.strip() or tick < 0:
            raise ValueError("tradition name and non-negative tick are required")
        self.traditions[name] = tick

    def recent(self, limit: int = 10) -> tuple[HistoricalEvent, ...]:
        if limit < 0:
            raise ValueError("limit cannot be negative")
        return tuple(self.events[-limit:]) if limit else ()
