from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SocialGroup:
    group_id: str
    name: str
    members: set[str] = field(default_factory=set)
    norms: dict[str, float] = field(default_factory=dict)

    def add(self, agent_id: str) -> None:
        if not agent_id.strip():
            raise ValueError("agent_id cannot be empty")
        self.members.add(agent_id)

    def remove(self, agent_id: str) -> None:
        self.members.discard(agent_id)
