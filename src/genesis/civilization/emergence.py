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
    """Derived civilization-stage transitions from canonical civilization state."""
    stages: dict[str, CivilizationStage] = field(default_factory=dict)
    transitions: list[CivilizationTransition] = field(default_factory=list)
    max_history: int = 20_000
    _ORDER = tuple(CivilizationStage)

    def __post_init__(self) -> None:
        if self.max_history < 1:
            raise ValueError("max_history must be positive")

    @staticmethod
    def _clamp(value: float) -> float:
        if not (value == value and value not in (float("inf"), float("-inf"))):
            raise ValueError("civilization signal must be finite")
        return max(0.0, min(1.0, value))

    def _stage(self, value: CivilizationStage) -> int:
        return self._ORDER.index(value)

    def signal(self, state: SimulationState, settlement_id: str, tick: int) -> CivilizationSignal:
        if tick < 0:
            raise ValueError("tick cannot be negative")
        settlement = state.civilization.settlements.get(settlement_id)
        if settlement is None:
            raise KeyError(settlement_id)
        members = [state.agents[agent_id] for agent_id in settlement.population if agent_id in state.agents and state.agents[agent_id].health > 0.0]
        population = len(members)
        food_security = self._clamp(max(0.0, float(settlement.stored_resources.get("food", 0.0))) / max(1.0, population * 2.0))
        knowledge = self._clamp(sum(len(agent.knowledge) for agent in members) / max(1.0, population * 10.0))
        social_cohesion = self._clamp(sum(float(agent.personality.cooperation) for agent in members) / max(1.0, population))
        economic_capacity = self._clamp(sum(float(agent.wealth) for agent in members) / max(1.0, population * 100.0))
        infrastructure = self._clamp(len(settlement.buildings) / max(1.0, population / 2.0))
        environmental_pressure = self._clamp((1.0 - food_security) * 0.7 + (1.0 - social_cohesion) * 0.3)
        return CivilizationSignal(tick, population, food_security, knowledge, social_cohesion, economic_capacity, infrastructure, environmental_pressure)

    def _candidate(self, signal: CivilizationSignal) -> CivilizationStage:
        capacity = 0.30 * signal.food_security + 0.20 * signal.knowledge + 0.20 * signal.social_cohesion + 0.15 * signal.economic_capacity + 0.15 * signal.infrastructure
        if signal.population >= 100 and capacity >= 0.70: return CivilizationStage.CIVILIZATION
        if signal.population >= 50 and capacity >= 0.58: return CivilizationStage.CITY
        if signal.population >= 25 and capacity >= 0.48: return CivilizationStage.TOWN
        if signal.population >= 12 and capacity >= 0.38: return CivilizationStage.VILLAGE
        if signal.population >= 5 and capacity >= 0.28: return CivilizationStage.SETTLEMENT
        if signal.population >= 2: return CivilizationStage.CAMP
        return CivilizationStage.SURVIVAL

    def step(self, state: SimulationState, tick: int) -> tuple[CivilizationTransition, ...]:
        transitions: list[CivilizationTransition] = []
        for settlement_id in sorted(state.civilization.settlements):
            signal = self.signal(state, settlement_id, tick)
            previous = self.stages.get(settlement_id, CivilizationStage.SURVIVAL)
            candidate = self._candidate(signal)
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
