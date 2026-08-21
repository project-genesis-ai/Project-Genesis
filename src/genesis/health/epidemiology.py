from __future__ import annotations

from dataclasses import dataclass, field
import random

from .health import Disease, HealthState

@dataclass(frozen=True, slots=True)
class Contact:
    source_id: str
    target_id: str
    contacts_per_day: float
    hygiene_factor: float = 1.0

    def __post_init__(self) -> None:
        if not self.source_id.strip() or not self.target_id.strip() or self.contacts_per_day < 0 or not 0.0 <= self.hygiene_factor <= 1.0:
            raise ValueError("invalid contact")

@dataclass(slots=True)
class Epidemiology:
    states: dict[str, HealthState] = field(default_factory=dict)
    rng: random.Random = field(default_factory=random.Random)

    def register(self, agent_id: str, state: HealthState | None = None) -> HealthState:
        if agent_id in self.states:
            raise ValueError(f"health state already exists: {agent_id}")
        value = state or HealthState()
        self.states[agent_id] = value
        return value

    def vaccinate(self, agent_id: str, disease_id: str) -> None:
        self._state(agent_id).immunity.add(disease_id)

    def expose(self, contact: Contact, disease: Disease, days: float = 1.0) -> bool:
        if days < 0:
            raise ValueError("days cannot be negative")
        source = self._state(contact.source_id)
        target = self._state(contact.target_id)
        if disease.disease_id not in source.diseases:
            return False
        if disease.disease_id in target.immunity or disease.disease_id in target.diseases:
            return False
        # Independent-contact approximation: P(no transmission)=exp(-lambda * contacts * days).
        hazard = disease.transmission * contact.contacts_per_day * days * contact.hygiene_factor
        probability = 1.0 - pow(2.718281828459045, -hazard)
        if self.rng.random() < probability:
            return target.infect(disease)
        return False

    def _state(self, agent_id: str) -> HealthState:
        try:
            return self.states[agent_id]
        except KeyError as exc:
            raise KeyError(f"unknown health state: {agent_id}") from exc
