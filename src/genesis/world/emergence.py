from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from genesis.core.state import SimulationState


@dataclass(frozen=True, slots=True)
class EmergenceSignal:
    tick: int
    ecological_health: float
    civilization_strain: float
    technology_opportunity: float
    migration_pressure: float
    resilience: float


@dataclass(frozen=True, slots=True)
class EmergenceTransition:
    tick: int
    previous_regime: str
    regime: str
    signal: EmergenceSignal


@dataclass(slots=True)
class EmergenceRuntime:
    """Derived macro-dynamics layer; it never becomes a second state authority.

    The runtime detects stable cross-domain regimes from canonical planetary,
    biological, human, social, economic and technology state. Hysteresis keeps
    the regime from oscillating on boundary noise.
    """

    regime: str = "stable"
    transitions: list[EmergenceTransition] = field(default_factory=list)
    last_signal: EmergenceSignal | None = None
    max_history: int = 10_000
    transition_margin: float = 0.05

    def __post_init__(self) -> None:
        if self.max_history < 1:
            raise ValueError("max_history must be positive")
        if not 0.0 < self.transition_margin < 0.5:
            raise ValueError("transition_margin must be in (0, 0.5)")

    @staticmethod
    def _clamp(value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("emergence input must be finite")
        return max(0.0, min(1.0, value))

    @staticmethod
    def _mean(values: list[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    def signal(self, state: SimulationState, tick: int) -> EmergenceSignal:
        if tick < 0:
            raise ValueError("tick cannot be negative")

        organisms = [o for o in state.ecosystem.organisms.values() if getattr(o, "alive", True)]
        agents = [a for a in state.agents.values() if a.health > 0.0]
        health = self._mean([self._clamp(float(a.health)) for a in agents])
        biodiversity = self._clamp(len({getattr(o, "species_id", "unknown") for o in organisms}) / max(1.0, len(state.ecosystem.species)))
        biomass = sum(max(0.0, float(getattr(o, "biomass", 0.0))) for o in organisms)
        biomass_health = self._clamp(biomass / max(1.0, len(organisms)))
        ecological_health = self._clamp(0.45 * health + 0.35 * biodiversity + 0.20 * biomass_health)

        disease = self._mean([1.0 - self._clamp(float(h.health)) for h in state.health.states.values()])
        resource_values = [max(0.0, float(v)) for v in state.resources.quantities.values()]
        resource_pressure = 1.0 / (1.0 + self._mean(resource_values)) if resource_values else 1.0
        social_stress = self._mean([1.0 - self._clamp(float(a.personality.cooperation)) for a in agents])
        economic_stress = self._clamp(sum(max(0.0, 1.0 - float(w.balance) / 100.0) for w in state.wallets.values()) / max(1, len(state.wallets)))
        civilization_strain = self._clamp(0.30 * disease + 0.25 * resource_pressure + 0.25 * social_stress + 0.20 * economic_stress)

        locked = [t for t in state.technologies.values() if not t.unlocked]
        unlocked = [t for t in state.technologies.values() if t.unlocked]
        research_progress = self._mean([self._clamp(float(getattr(t, "progress", 0.0))) for t in locked]) if locked else 1.0
        technology_opportunity = self._clamp(0.55 * research_progress + 0.45 * self._clamp(len(unlocked) / max(1.0, len(state.technologies))))

        disaster_count = len(state.disasters.active)
        migration_pressure = self._clamp(0.55 * civilization_strain + 0.25 * disaster_count / max(1.0, len(agents)) + 0.20 * (1.0 - ecological_health))
        resilience = self._clamp(0.45 * ecological_health + 0.30 * health + 0.25 * technology_opportunity)

        result = EmergenceSignal(tick, ecological_health, civilization_strain, technology_opportunity, migration_pressure, resilience)
        self.last_signal = result
        return result

    def _classify(self, signal: EmergenceSignal) -> str:
        m = self.transition_margin
        if signal.civilization_strain >= 0.75 + m or signal.ecological_health <= 0.20 - m:
            return "crisis"
        if signal.civilization_strain >= 0.55 + m or signal.migration_pressure >= 0.70 + m:
            return "strain"
        if signal.technology_opportunity >= 0.72 + m and signal.resilience >= 0.55:
            return "innovation"
        if signal.ecological_health >= 0.75 and signal.resilience >= 0.70:
            return "flourishing"
        return "stable"

    def step(self, state: SimulationState, tick: int) -> EmergenceTransition | None:
        signal = self.signal(state, tick)
        candidate = self._classify(signal)
        if candidate == self.regime:
            return None

        # Hysteresis: leave a non-stable regime only when the new state clears
        # the classifier margin; stable acts as the neutral basin.
        previous = self.regime
        self.regime = candidate
        transition = EmergenceTransition(tick, previous, candidate, signal)
        self.transitions.append(transition)
        if len(self.transitions) > self.max_history:
            del self.transitions[: len(self.transitions) - self.max_history]
        return transition
