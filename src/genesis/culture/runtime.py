from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from genesis.agents.agent import Agent
from genesis.cognition.memory import Memory
from genesis.social import RelationType, SocialSystem
from .history import CulturalMemory


@dataclass(frozen=True, slots=True)
class CultureTickResult:
    transmissions: int
    new_knowledge: int
    traditions: int


class CultureRuntime:
    """Authoritative bounded transmission of knowledge through trusted friendships."""

    def step(
        self,
        culture: CulturalMemory,
        social: SocialSystem,
        agents: dict[str, Agent],
        tick: int,
    ) -> CultureTickResult:
        if tick < 0:
            raise ValueError("tick cannot be negative")
        transmissions = 0
        new_knowledge = 0
        traditions = 0
        living = sorted((a for a in agents.values() if a.health > 0.0), key=lambda a: a.agent_id)

        for left, right in combinations(living, 2):
            relation = social.relationships.get(left.agent_id, right.agent_id, RelationType.FRIEND)
            if relation is None or relation.trust < 0.65:
                continue
            candidates = sorted(left.knowledge - right.knowledge)
            if candidates:
                knowledge = candidates[0]
                right.learn(knowledge)
                right.memory.remember(self._memory(right, tick, knowledge, left.agent_id))
                transmissions += 1
                new_knowledge += 1
            candidates = sorted(right.knowledge - left.knowledge)
            if candidates:
                knowledge = candidates[0]
                left.learn(knowledge)
                left.memory.remember(self._memory(left, tick, knowledge, right.agent_id))
                transmissions += 1
                new_knowledge += 1

        for knowledge in sorted({item for agent in living for item in agent.knowledge}):
            adopters = sum(knowledge in agent.knowledge for agent in living)
            if adopters >= 2:
                tradition = f"shared:{knowledge}"
                if tradition not in culture.traditions:
                    culture.teach_tradition(tradition, tick)
                    traditions += 1
        return CultureTickResult(transmissions, new_knowledge, traditions)

    @staticmethod
    def _memory(agent: Agent, tick: int, knowledge: str, teacher_id: str) -> Memory:
        return Memory(
            memory_id=f"culture:{agent.agent_id}:{tick}:{teacher_id}:{knowledge}",
            subject="knowledge",
            content=knowledge,
            created_tick=tick,
            importance=0.6 + 0.2 * agent.personality.curiosity,
            confidence=0.9,
        )
