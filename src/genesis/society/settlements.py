from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Settlement:
    settlement_id: str
    name: str
    population: set[str] = field(default_factory=set)
    buildings: set[str] = field(default_factory=set)
    resources: dict[str, float] = field(default_factory=dict)

    def add_resident(self, agent_id: str) -> None:
        self.population.add(agent_id)

    def remove_resident(self, agent_id: str) -> None:
        self.population.discard(agent_id)

    @property
    def population_count(self) -> int:
        return len(self.population)
