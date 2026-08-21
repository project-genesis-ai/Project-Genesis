from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from genesis.agents.agent import Agent
from .relationships import RelationType, Relationship
from .social import SocialSystem


@dataclass(frozen=True, slots=True)
class SocialTickResult:
    interactions: int
    trust_changes: int
    friendships: int
    rivalries: int


class SocialRuntime:
    """Authoritative deterministic bridge from agent traits to social state."""

    def step(self, social: SocialSystem, agents: dict[str, Agent], tick: int) -> SocialTickResult:
        if tick < 0:
            raise ValueError("tick cannot be negative")

        living = [agent for agent in agents.values() if agent.health > 0.0]
        living.sort(key=lambda agent: agent.agent_id)
        interactions = trust_changes = friendships = rivalries = 0

        for left, right in combinations(living, 2):
            compatibility = (
                0.35 * (1.0 - abs(left.personality.cooperation - right.personality.cooperation))
                + 0.25 * (1.0 - abs(left.personality.patience - right.personality.patience))
                + 0.20 * (1.0 - abs(left.personality.curiosity - right.personality.curiosity))
                + 0.20 * (1.0 - abs(left.personality.risk_tolerance - right.personality.risk_tolerance))
            )
            stress = (left.needs.hunger + left.needs.thirst + right.needs.hunger + right.needs.thirst) / 4.0
            positive = max(0.0, compatibility * (1.0 - 0.5 * stress))
            negative = max(0.0, (1.0 - compatibility) * stress)

            existing = social.relationships.get(left.agent_id, right.agent_id, RelationType.FRIEND)
            if existing is None:
                existing = social.relationships.get(left.agent_id, right.agent_id, RelationType.RIVAL)
            if existing is None:
                existing = Relationship(left.agent_id, right.agent_id, RelationType.FRIEND, trust=0.5, affinity=0.0)
                social.relationships.connect(existing)
                reverse = Relationship(right.agent_id, left.agent_id, RelationType.FRIEND, trust=0.5, affinity=0.0)
                social.relationships.connect(reverse)

            before_trust = existing.trust
            existing.interact(positive=positive, negative=negative)
            interactions += 1
            if existing.trust != before_trust:
                trust_changes += 1

            if existing.affinity >= 0.35 and positive >= 0.45:
                existing.relation = RelationType.FRIEND
                reverse = social.relationships.get(right.agent_id, left.agent_id, RelationType.FRIEND)
                if reverse is None:
                    social.relationships.connect(Relationship(right.agent_id, left.agent_id, RelationType.FRIEND, existing.trust, existing.affinity, existing.interaction_count))
                friendships += 1
            elif existing.affinity <= -0.35 and negative > positive:
                existing.relation = RelationType.RIVAL
                rival = social.relationships.get(right.agent_id, left.agent_id, RelationType.RIVAL)
                if rival is None:
                    social.relationships.connect(Relationship(right.agent_id, left.agent_id, RelationType.RIVAL, existing.trust, existing.affinity, existing.interaction_count))
                rivalries += 1

        self._update_groups(social, living)
        return SocialTickResult(interactions, trust_changes, friendships, rivalries)

    @staticmethod
    def _update_groups(social: SocialSystem, agents: list[Agent]) -> None:
        by_id = {agent.agent_id: agent for agent in agents}
        for group in social.groups.values():
            for agent_id in tuple(group.members):
                if agent_id not in by_id:
                    group.leave(agent_id)
            if group.members:
                values = [group.reputation.get(agent_id, 0.0) for agent_id in group.members]
                group.cohesion = max(0.0, min(1.0, 0.5 + sum(values) / max(1, len(values)) * 0.5))

        for left, right in combinations(sorted(agents, key=lambda a: a.agent_id), 2):
            relation = social.relationships.get(left.agent_id, right.agent_id, RelationType.FRIEND)
            if relation is None or relation.affinity < 0.35:
                continue
            group_id = f"friendship:{min(left.agent_id, right.agent_id)}:{max(left.agent_id, right.agent_id)}"
            group = social.groups.get(group_id)
            if group is None:
                from .social import SocialGroup
                group = SocialGroup(group_id=group_id)
                social.groups[group_id] = group
            group.join(left.agent_id)
            group.join(right.agent_id)
