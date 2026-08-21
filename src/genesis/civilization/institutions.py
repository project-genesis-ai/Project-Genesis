from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Institution:
    institution_id: str
    name: str
    members: set[str] = field(default_factory=set)
    rules: dict[str, float] = field(default_factory=dict)

    def add_member(self, agent_id: str) -> None:
        self.members.add(agent_id)

    def remove_member(self, agent_id: str) -> None:
        self.members.discard(agent_id)
