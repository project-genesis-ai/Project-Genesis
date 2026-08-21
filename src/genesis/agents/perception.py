from __future__ import annotations

from dataclasses import dataclass

from genesis.agents.agent import Agent
from genesis.world.world import WorldState


@dataclass(frozen=True, slots=True)
class Perception:
    agent_id: str
    tick: int
    nearby_resources: tuple[str, ...]


def perceive(agent: Agent, world: WorldState, tick: int) -> Perception:
    """Return bounded local resource knowledge; global agent state is not leaked."""
    resources = tuple(sorted(name for name, amount in world.resources.items() if amount > 0.0))
    return Perception(agent.agent_id, tick, resources)
