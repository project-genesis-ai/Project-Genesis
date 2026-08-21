from __future__ import annotations

from .forest import ForestDynamics
from .ecosystem import Ecosystem
from genesis.world.environment import Environment


class LifeSystem:
    """Coordinates environment-driven vegetation and organism lifecycle updates."""

    def __init__(self, forest: ForestDynamics | None = None) -> None:
        self.forest = forest or ForestDynamics()

    def step(self, environment: Environment, ecosystem: Ecosystem, ticks: int) -> None:
        if ticks < 0:
            raise ValueError("ticks cannot be negative")
        for cell in environment.cells.values():
            self.forest.step(cell, ticks)
        ecosystem.step(ticks)
