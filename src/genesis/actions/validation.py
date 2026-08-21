from __future__ import annotations

from genesis.agents.agent import Agent
from genesis.core.clock import SimulationTime
from genesis.world.world import WorldState

from .base import Action


def validate_action(action: Action, agent: Agent, world: WorldState, time: SimulationTime) -> None:
    """Run the action's preconditions before execution."""
    action.validate(agent, world, time)
