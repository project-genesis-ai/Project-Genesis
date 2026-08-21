from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from genesis.agents.needs import Needs


@dataclass(frozen=True, slots=True)
class Injury:
    injury_id: str
    severity: float
    recovery_ticks: int

    def __post_init__(self) -> None:
        if not self.injury_id.strip() or not 0.0 <= self.severity <= 1.0 or self.recovery_ticks < 1:
            raise ValueError("invalid injury")


@dataclass(frozen=True, slots=True)
class Disease:
    disease_id: str
    severity: float
    transmission: float = 0.0
    duration_ticks: int = 1

    def __post_init__(self) -> None:
        if not self.disease_id.strip() or not 0.0 <= self.severity <= 1.0 or not 0.0 <= self.transmission <= 1.0 or self.duration_ticks < 1:
            raise ValueError("invalid disease")


@dataclass(slots=True)
class HealthState:
    health: float = 1.0
    injuries: dict[str, Injury] = field(default_factory=dict)
    diseases: dict[str, int] = field(default_factory=dict)
    immunity: set[str] = field(default_factory=set)
    needs: Needs | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.health <= 1.0:
            raise ValueError("health must be between 0 and 1")

    @property
    def alive(self) -> bool:
        return self.health > 0.0

    def injure(self, injury: Injury) -> None:
        self.injuries[injury.injury_id] = injury
        self.health = max(0.0, self.health - injury.severity * 0.5)

    def infect(self, disease: Disease) -> bool:
        if disease.disease_id in self.immunity or disease.disease_id in self.diseases:
            return False
        self.diseases[disease.disease_id] = disease.duration_ticks
        self.health = max(0.0, self.health - disease.severity * 0.1)
        return True


@dataclass(slots=True)
class HealthSystem:
    states: dict[str, HealthState] = field(default_factory=dict)

    def register(self, agent_id: str, state: HealthState | None = None) -> HealthState:
        if not agent_id.strip():
            raise ValueError("agent_id cannot be empty")
        if agent_id in self.states:
            raise ValueError(f"health state already exists: {agent_id}")
        value = state or HealthState()
        self.states[agent_id] = value
        return value

    def step(self, ticks: int = 1, recovery_rate: float = 0.01, need_damage_rate: float = 0.02) -> None:
        if ticks < 0 or recovery_rate < 0.0 or need_damage_rate < 0.0:
            raise ValueError("ticks and health rates cannot be negative")
        for state in self.states.values():
            for injury_id, injury in list(state.injuries.items()):
                remaining = max(0, injury.recovery_ticks - ticks)
                if remaining == 0:
                    del state.injuries[injury_id]
                else:
                    state.injuries[injury_id] = Injury(injury.injury_id, injury.severity, remaining)
            for disease_id, remaining in list(state.diseases.items()):
                remaining -= ticks
                if remaining <= 0:
                    del state.diseases[disease_id]
                    state.immunity.add(disease_id)
            if not state.injuries and not state.diseases:
                state.health = min(1.0, state.health + recovery_rate * ticks)
            if state.needs is not None and need_damage_rate > 0.0:
                state.health = max(0.0, state.health - state.needs.health_pressure() * need_damage_rate * ticks)
