from __future__ import annotations

from dataclasses import dataclass

from genesis.actions.base import ActionResult
from genesis.agents.agent import Agent
from genesis.core.clock import SimulationTime
from genesis.world.world import WorldState


@dataclass(frozen=True, slots=True)
class ConsumeResource:
    """Consume one inventory unit and satisfy the matching survival need."""

    resource_name: str
    need_name: str
    relief: float = 0.5
    name: str = "consume_resource"

    def validate(self, agent: Agent, world: WorldState, time: SimulationTime) -> None:
        if not self.resource_name.strip():
            raise ValueError("resource_name cannot be empty")
        if not hasattr(agent.needs, self.need_name):
            raise ValueError(f"Unknown need: {self.need_name}")
        if self.relief <= 0.0 or self.relief > 1.0:
            raise ValueError("relief must be in (0, 1]")
        if agent.inventory.get(self.resource_name, 0.0) < 1.0:
            raise ValueError(f"Missing inventory resource: {self.resource_name}")

    def execute(self, agent: Agent, world: WorldState, time: SimulationTime) -> ActionResult:
        self.validate(agent, world, time)
        agent.inventory[self.resource_name] -= 1.0
        if agent.inventory[self.resource_name] <= 0.0:
            del agent.inventory[self.resource_name]
        current = getattr(agent.needs, self.need_name)
        setattr(agent.needs, self.need_name, max(0.0, current - self.relief))
        return ActionResult(success=True)
