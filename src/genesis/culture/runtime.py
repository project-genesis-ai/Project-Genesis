from __future__ import annotations

from dataclasses import dataclass

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
        living_ids = {agent_id for agent_id, agent in agents.items() if agent.health > 0.0}
        friend_edges = sorted(
            (
                relation.source_id,
                relation.target_id,
                relation,
            )
            for relation in social.relationships.relationships.values()
            if relation.relation is RelationType.FRIEND
            and relation.source_id in living_ids
            and relation.target_id in living_ids
            and relation.source_id < relation.target_id
            and relation.trust >= 0.65
        )

        for left_id, right_id, relation in friend_edges:
            left = agents[left_id]
            right = agents[right_id]
            candidates = sorted(left.knowledge - right.knowledge)
            if candidates:
                knowledge = candidates[0]
                right.learn(knowledge)
                right.memory.remember(self._memory(right, tick, knowledge, left_id))
                transmissions += 1
                new_knowledge += 1
            candidates = sorted(right.knowledge - left.knowledge)
            if candidates:
                knowledge = candidates[0]
                left.learn(knowledge)
                left.memory.remember(self._memory(left, tick, knowledge, right_id))
                transmissions += 1
                new_knowledge += 1

        for knowledge in sorted({item for agent_id in living_ids for item in agents[agent_id].knowledge}):
            adopters = sum(knowledge in agents[agent_id].knowledge for agent_id in living_ids)
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
