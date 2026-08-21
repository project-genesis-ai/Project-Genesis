from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from genesis.core.state import SimulationState


class CivilizationStage(str, Enum):
    SURVIVAL = "survival"
    CAMP = "camp"
    SETTLEMENT = "settlement"
    VILLAGE = "village"
    TOWN = "town"
    CITY = "city"
    CIVILIZATION = "civilization"


@dataclass(frozen=True, slots=True)
class CivilizationSignal:
    tick: int
    population: int
    food_security: float
    knowledge: float
    social_cohesion: float
    economic_capacity: float
    infrastructure: float
    environmental_pressure: float


@dataclass(frozen=True, slots=True)
class CivilizationTransition:
    tick: int
    settlement_id: str
    previous_stage: CivilizationStage
    stage: CivilizationStage
    signal: CivilizationSignal


@dataclass(slots=True)
class CivilizationEmergenceRuntime:
    """Derived civilization-stage transitions from canonical settlement state."""

    stages: dict[str, CivilizationStage] = field(default_factory=dict)
    transitions: list[CivilizationTransition] = field(default_factory=list)
    max_history: int = 20_000

    _ORDER = tuple(CivilizationStage)

    def _stage(self, value: CivilizationStage) -> int:
        return self._ORDER.index(value)

    @staticmethod
    def _clamp(value: float) -> float:
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError("civilization signal must be finite")
        return max(0.0, min(1.0, value))

    def signal(self, state: SimulationState, settlement_id: str, tick: int) -> CivilizationSignal:
        settlement = state.settlements.get(settlement_id)
        if settlement is None:
            raise KeyError(settlement_id)
        members = [a for a in state.agents.values() if a.health > 0.0 and getattr(a, "settlement_id", settlement_id) == settlement_id]
        population = len(members)
        food = self._clamp(sum(max(0.0, float(a.inventory.get("food", 0.0))) for a in members) / max(1.0, population * 2.0))
        knowledge = self._clamp(sum(len(a.knowledge) for a in members) / max(1.0, population * 10.0))
        cooperation = self._clamp(sum(float(a.personality.cooperation) for a in members) / max(1.0, population))
        wealth = self._clamp(sum(float(a.wealth) for a in members) / max(1.0, population * 100.0))
        infrastructure = self._clamp(float(getattr(settlement, "level", 0)) / 10.0)
        pressure = self._clamp(max(0.0, 1.0 - food) * 0.7 + max(0.0, 1.0 - cooperation) * 0.3)
        return CivilizationSignal(tick, population, food, knowledge, cooperation, wealth, infrastructure, pressure)

    def _candidate(self, signal: CivilizationSignal) -> CivilizationStage:
        p = signal.population
        capacity = (
            0.30 * signal.food_security
            + 0.20 * signal.knowledge
            + 0.20 * signal.social_cohesion
            + 0.15 * signal.economic_capacity
            + 0.15 * signal.infrastructure
        )
        if p >= 100 and capacity >= 0.70: return CivilizationStage.CIVILIZATION
        if p >= 50 and capacity >= 0.58: return CivilizationStage.CITY
        if p >= 25 and capacity >= 0.48: return CivilizationStage.TOWN
        if p >= 12 and capacity >= 0.38: return CivilizationStage.VILLAGE
        if p >= 5 and capacity >= 0.28: return CivilizationStage.SETTLEMENT
        if p >= 2: return CivilizationStage.CAMP
        return CivilizationStage.SURVIVAL

    def step(self, state: SimulationState, tick: int) -> tuple[CivilizationTransition, ...]:
        transitions: list[CivilizationTransition] = []
        for settlement_id in sorted(state.settlements):
            signal = self.signal(state, settlement_id, tick)
            previous = self.stages.get(settlement_id, CivilizationStage.SURVIVAL)
            candidate = self._candidate(signal)
            # Prevent unrealistic multi-level jumps; emergence advances one stage per tick.
            if self._stage(candidate) > self._stage(previous) + 1:
                candidate = self._ORDER[self._stage(previous) + 1]
            if candidate is previous:
                continue
            self.stages[settlement_id] = candidate
            transition = CivilizationTransition(tick, settlement_id, previous, candidate, signal)
            transitions.append(transition)
            self.transitions.append(transition)
        if len(self.transitions) > self.max_history:
            del self.transitions[:len(self.transitions) - self.max_history]
        return tuple(transitions)
