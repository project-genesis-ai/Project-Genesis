from __future__ import annotations

from dataclasses import dataclass, field

from .relationships import Relationship, RelationshipGraph, RelationType


@dataclass(slots=True)
class Household:
    household_id: str
    members: set[str] = field(default_factory=set)
    resources: dict[str, float] = field(default_factory=dict)

    def add_member(self, agent_id: str) -> None:
        if not agent_id.strip():
            raise ValueError("agent_id cannot be empty")
        self.members.add(agent_id)

    def remove_member(self, agent_id: str) -> None:
        self.members.discard(agent_id)


@dataclass(slots=True)
class SocialGroup:
    group_id: str
    members: set[str] = field(default_factory=set)
    cohesion: float = 0.5
    reputation: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.group_id.strip():
            raise ValueError("group_id cannot be empty")
        if not 0.0 <= self.cohesion <= 1.0:
            raise ValueError("cohesion must be between 0 and 1")

    def join(self, agent_id: str) -> None:
        if not agent_id.strip():
            raise ValueError("agent_id cannot be empty")
        self.members.add(agent_id)
        self.reputation.setdefault(agent_id, 0.0)

    def leave(self, agent_id: str) -> None:
        self.members.discard(agent_id)
        self.reputation.pop(agent_id, None)

    def update_reputation(self, agent_id: str, delta: float) -> None:
        if agent_id not in self.members:
            raise ValueError("agent must be a group member")
        self.reputation[agent_id] = max(-1.0, min(1.0, self.reputation.get(agent_id, 0.0) + delta))


@dataclass(slots=True)
class SocialSystem:
    relationships: RelationshipGraph = field(default_factory=RelationshipGraph)
    households: dict[str, Household] = field(default_factory=dict)
    groups: dict[str, SocialGroup] = field(default_factory=dict)

    def establish_family(self, parent_id: str, child_id: str) -> None:
        if parent_id == child_id:
            raise ValueError("family members must be distinct")
        self.relationships.connect(Relationship(parent_id, child_id, RelationType.PARENT))
        self.relationships.connect(Relationship(child_id, parent_id, RelationType.CHILD))
