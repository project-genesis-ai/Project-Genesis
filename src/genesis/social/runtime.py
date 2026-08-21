from __future__ import annotations

from dataclasses import dataclass

from genesis.agents.agent import Agent
from .relationships import RelationType, Relationship
from .social import SocialGroup, SocialSystem


@dataclass(frozen=True, slots=True)
class SocialTickResult:
    interactions: int
    trust_changes: int
    friendships: int
    rivalries: int


class SocialRuntime:
    """Authoritative deterministic social runtime with bounded per-tick work."""

    def __init__(self, max_interactions_per_agent: int = 8) -> None:
        if max_interactions_per_agent < 1:
            raise ValueError("max_interactions_per_agent must be positive")
        self.max_interactions_per_agent = max_interactions_per_agent

    def step(self, social: SocialSystem, agents: dict[str, Agent], tick: int) -> SocialTickResult:
        if tick < 0:
            raise ValueError("tick cannot be negative")

        living = sorted((agent for agent in agents.values() if agent.health > 0.0), key=lambda a: a.agent_id)
        interactions = trust_changes = friendships = rivalries = 0
        if len(living) < 2:
            self._update_groups(social, living)
            return SocialTickResult(0, 0, 0, 0)

        pair_keys: set[tuple[str, str]] = set()
        limit = min(self.max_interactions_per_agent, len(living) - 1)
        for index, left in enumerate(living):
            for offset in range(1, limit + 1):
                right = living[(index + offset) % len(living)]
                if left.agent_id == right.agent_id:
                    continue
                pair_keys.add(tuple(sorted((left.agent_id, right.agent_id))))

        by_id = {agent.agent_id: agent for agent in living}
        for left_id, right_id in sorted(pair_keys):
            left = by_id[left_id]
            right = by_id[right_id]
            compatibility = (
                0.35 * (1.0 - abs(left.personality.cooperation - right.personality.cooperation))
                + 0.25 * (1.0 - abs(left.personality.patience - right.personality.patience))
                + 0.20 * (1.0 - abs(left.personality.curiosity - right.personality.curiosity))
                + 0.20 * (1.0 - abs(left.personality.risk_tolerance - right.personality.risk_tolerance))
            )
            stress = (left.needs.hunger + left.needs.thirst + right.needs.hunger + right.needs.thirst) / 4.0
            positive = max(0.0, compatibility * (1.0 - 0.5 * stress))
            negative = max(0.0, (1.0 - compatibility) * stress)

            relation = social.relationships.get(left_id, right_id, RelationType.FRIEND)
            if relation is None:
                relation = social.relationships.get(left_id, right_id, RelationType.RIVAL)
            if relation is None:
                relation = Relationship(left_id, right_id, RelationType.FRIEND)
                social.relationships.connect(relation)
                social.relationships.connect(Relationship(right_id, left_id, RelationType.FRIEND))

            before_trust = relation.trust
            relation.interact(positive=positive, negative=negative)
            interactions += 1
            trust_changes += int(relation.trust != before_trust)

            if relation.affinity >= 0.35 and positive >= 0.45:
                friendships += 1
            elif relation.affinity <= -0.35 and negative > positive:
                rivalries += 1
                if social.relationships.get(left_id, right_id, RelationType.RIVAL) is None:
                    social.relationships.connect(Relationship(
                        left_id, right_id, RelationType.RIVAL,
                        trust=relation.trust, affinity=relation.affinity,
                        interaction_count=relation.interaction_count,
                    ))
                    social.relationships.connect(Relationship(
                        right_id, left_id, RelationType.RIVAL,
                        trust=relation.trust, affinity=relation.affinity,
                        interaction_count=relation.interaction_count,
                    ))

        self._update_groups(social, living)
        return SocialTickResult(interactions, trust_changes, friendships, rivalries)

    @staticmethod
    def _update_groups(social: SocialSystem, agents: list[Agent]) -> None:
        living_ids = {agent.agent_id for agent in agents}
        for group in social.groups.values():
            for agent_id in tuple(group.members):
                if agent_id not in living_ids:
                    group.leave(agent_id)
            if group.members:
                values = [group.reputation.get(agent_id, 0.0) for agent_id in group.members]
                group.cohesion = max(0.0, min(1.0, 0.5 + sum(values) / max(1, len(values)) * 0.5))

        for relation in tuple(social.relationships.relationships.values()):
            if relation.relation is not RelationType.FRIEND or relation.affinity < 0.35:
                continue
            if relation.source_id not in living_ids or relation.target_id not in living_ids:
                continue
            left_id, right_id = sorted((relation.source_id, relation.target_id))
            if relation.source_id != left_id:
                continue
            group_id = f"friendship:{left_id}:{right_id}"
            group = social.groups.setdefault(group_id, SocialGroup(group_id=group_id))
            group.join(left_id)
            group.join(right_id)
