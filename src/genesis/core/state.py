from __future__ import annotations

from dataclasses import dataclass, field

from genesis.agents.agent import Agent
from genesis.events.history import EventHistory
from genesis.life.ecosystem import Ecosystem
from genesis.physics.world import PhysicsWorld
from genesis.world.environment import Environment
from genesis.world.world import WorldState


@dataclass(slots=True)
class SimulationState:
    """Mutable authoritative state container for one simulation instance."""

    world: WorldState = field(default_factory=WorldState)
    environment: Environment = field(default_factory=Environment)
    physics: PhysicsWorld = field(default_factory=PhysicsWorld)
    ecosystem: Ecosystem = field(default_factory=Ecosystem)
    agents: dict[str, Agent] = field(default_factory=dict)
    history: EventHistory = field(default_factory=EventHistory)

    def add_agent(self, agent: Agent) -> None:
        if agent.agent_id in self.agents:
            raise ValueError(f"Agent already exists: {agent.agent_id}")
        self.agents[agent.agent_id] = agent
