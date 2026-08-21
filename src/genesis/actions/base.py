from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from genesis.agents.agent import Agent
from genesis.core.clock import SimulationTime
from genesis.world.world import WorldState


@dataclass(frozen=True, slots=True)
class ActionResult:
    success: bool
    reason: str | None = None


class Action(Protocol):
    name: str

    def validate(self, agent: Agent, world: WorldState, time: SimulationTime) -> None: ...

    def execute(self, agent: Agent, world: WorldState, time: SimulationTime) -> ActionResult: ...
