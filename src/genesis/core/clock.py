from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SimulationTime:
    """Discrete simulation time measured in ticks."""

    tick: int = 0

    def __post_init__(self) -> None:
        if self.tick < 0:
            raise ValueError("Simulation time cannot be negative")

    def advance(self, ticks: int = 1) -> "SimulationTime":
        if ticks < 0:
            raise ValueError("Simulation cannot move backwards")
        return SimulationTime(self.tick + ticks)
