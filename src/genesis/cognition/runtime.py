from __future__ import annotations

from dataclasses import dataclass

from genesis.agents.agent import Agent
from genesis.agents.perception import Perception, perceive
from genesis.cognition.memory import Memory
from genesis.world.world import WorldState


@dataclass(frozen=True, slots=True)
class CognitionSnapshot:
    agent_id: str
    tick: int
    perception: Perception
    memory_count: int


class CognitionRuntime:
    """Authoritative bridge between perception, episodic memory and decisions.

    The runtime keeps cognition deterministic and bounded. It never mutates the
    world while observing it, and observations are stored only when they contain
    new information for the agent.
    """

    def observe(self, agent: Agent, world: WorldState, tick: int) -> CognitionSnapshot:
        perception = perceive(agent, world, tick)
        known = {memory.content for memory in agent.memory.memories if memory.subject == "resources"}
        resource_summary = ",".join(perception.nearby_resources)
        if resource_summary and resource_summary not in known:
            agent.memory.remember(
                Memory(
                    memory_id=f"obs:{agent.agent_id}:{tick}",
                    subject="resources",
                    content=resource_summary,
                    created_tick=tick,
                    importance=0.35 + 0.3 * agent.personality.curiosity,
                    confidence=1.0,
                )
            )
        return CognitionSnapshot(agent.agent_id, tick, perception, len(agent.memory.memories))

    def record_action(self, agent: Agent, tick: int, action: str, reason: str) -> None:
        agent.memory.remember(
            Memory(
                memory_id=f"action:{agent.agent_id}:{tick}:{action}",
                subject="actions",
                content=f"{action}:{reason}",
                created_tick=tick,
                importance=0.25 + 0.5 * agent.personality.patience,
                confidence=1.0,
            )
        )

    def record_outcome(self, agent: Agent, tick: int, outcome: str, importance: float = 0.5) -> None:
        if not outcome.strip():
            raise ValueError("outcome cannot be empty")
        agent.memory.remember(
            Memory(
                memory_id=f"outcome:{agent.agent_id}:{tick}",
                subject="outcomes",
                content=outcome,
                created_tick=tick,
                importance=max(0.0, min(1.0, importance)),
                confidence=1.0,
            )
        )
