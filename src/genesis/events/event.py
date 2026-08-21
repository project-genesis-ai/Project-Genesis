from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class SimulationEvent:
    """Immutable record of a meaningful simulation occurrence."""

    tick: int
    event_type: str
    actor_id: str | None = None
    target_id: str | None = None
    data: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.tick < 0:
            raise ValueError("Event tick cannot be negative")
        if not self.event_type.strip():
            raise ValueError("event_type cannot be empty")
