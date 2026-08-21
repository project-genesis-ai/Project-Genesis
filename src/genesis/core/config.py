from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    """Configuration that affects deterministic simulation execution."""

    seed: int = 0
    ticks_per_step: int = 1
    seconds_per_tick: float = 1.0

    def __post_init__(self) -> None:
        if self.ticks_per_step <= 0:
            raise ValueError("ticks_per_step must be positive")
        if self.seconds_per_tick <= 0.0:
            raise ValueError("seconds_per_tick must be positive")
