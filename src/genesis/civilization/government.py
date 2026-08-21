from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Government:
    government_id: str
    name: str
    population: set[str] = field(default_factory=set)
    laws: dict[str, float] = field(default_factory=dict)
    treasury: float = 0.0
    approval: float = 0.5
    public_services: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.government_id.strip() or not self.name.strip() or self.treasury < 0:
            raise ValueError("invalid government")
        if not 0.0 <= self.approval <= 1.0:
            raise ValueError("approval must be between 0 and 1")

    def add_citizen(self, agent_id: str) -> None:
        if not agent_id.strip():
            raise ValueError("agent_id cannot be empty")
        self.population.add(agent_id)

    def enact_law(self, name: str, strength: float = 1.0) -> None:
        if not name.strip() or not 0.0 <= strength <= 1.0:
            raise ValueError("invalid law")
        self.laws[name] = strength

    def collect_tax(self, amount: float) -> None:
        if amount < 0:
            raise ValueError("tax cannot be negative")
        self.treasury += amount

    def spend(self, service: str, amount: float) -> bool:
        if not service.strip() or amount < 0:
            raise ValueError("invalid service or amount")
        if amount > self.treasury:
            return False
        self.treasury -= amount
        self.public_services[service] = self.public_services.get(service, 0.0) + amount
        self.approval = min(1.0, self.approval + min(0.05, amount / 1000.0))
        return True

    def tick(self) -> None:
        if not self.population:
            return
        service_score = min(1.0, sum(self.public_services.values()) / max(1.0, len(self.population) * 10.0))
        law_burden = min(1.0, sum(self.laws.values()) / max(1, len(self.laws))) if self.laws else 0.0
        target = 0.5 + 0.4 * service_score - 0.1 * law_burden
        self.approval += (target - self.approval) * 0.1
