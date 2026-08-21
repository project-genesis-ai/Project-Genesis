from __future__ import annotations

from dataclasses import dataclass

from genesis.agents.agent import Agent
from genesis.world.world import WorldState


@dataclass(frozen=True, slots=True)
class Perception:
    agent_id: str
    tick: int
    visible_agents: tuple[str, ...]
    nearby_resources: tuple[str, ...]


def perceive(agent: Agent, world: WorldState, tick: int) -> Perception:
    """Return bounded local knowledge; global world state is never implicitly revealed."""
    visible = tuple(sorted(other_id for other_id in world.agents if other_id != agent.agent_id))
    resources = tuple(sorted(world.resources))
    return Perception(agent.agent_id, tick, visible, resources)
