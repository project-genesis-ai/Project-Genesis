from __future__ import annotations

from collections.abc import Iterable

from .event import SimulationEvent


class EventHistory:
    """Append-only in-memory event history for deterministic replay/debugging."""

    def __init__(self, events: Iterable[SimulationEvent] = ()) -> None:
        self._events = list(events)

    def append(self, event: SimulationEvent) -> None:
        if self._events and event.tick < self._events[-1].tick:
            raise ValueError("Events must be appended in non-decreasing tick order")
        self._events.append(event)

    def at_tick(self, tick: int) -> tuple[SimulationEvent, ...]:
        return tuple(event for event in self._events if event.tick == tick)

    def all(self) -> tuple[SimulationEvent, ...]:
        return tuple(self._events)

    def __getitem__(self, index: int | slice) -> SimulationEvent | tuple[SimulationEvent, ...]:
        """Provide deterministic read-only sequence-style access."""
        return self._events[index]

    def __len__(self) -> int:
        return len(self._events)

    def __iter__(self):
        return iter(self._events)
