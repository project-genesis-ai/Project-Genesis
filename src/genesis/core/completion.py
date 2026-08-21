from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING
import math

if TYPE_CHECKING:
    from genesis.core.simulation import Simulation


@dataclass(frozen=True, slots=True)
class RuntimeSignal:
    tick: int
    population: int
    living_species: int
    biomass: float
    water_stress: float
    climate_stress: float
    disease_pressure: float
    resource_stress: float
    social_cohesion: float
    economic_activity: float


@dataclass(slots=True)
class ScaleController:
    individual_threshold: int = 100_000
    aggregate_threshold: int = 1_000_000
    region_size: int = 32

    def __post_init__(self) -> None:
        if self.individual_threshold <= 0 or self.aggregate_threshold <= self.individual_threshold:
            raise ValueError("invalid population thresholds")
        if self.region_size <= 0:
            raise ValueError("region_size must be positive")

    def mode(self, population: int) -> str:
        if population < 0:
            raise ValueError("population cannot be negative")
        if population < self.individual_threshold:
            return "individual"
        if population < self.aggregate_threshold:
            return "hybrid"
        return "aggregate"

    def active_regions(self, population: int) -> int:
        if population < 0:
            raise ValueError("population cannot be negative")
        return 0 if population == 0 else max(1, math.ceil(population / self.individual_threshold))


@dataclass(slots=True)
class CompletionRuntime:
    """Cross-domain derived layer; existing subsystems remain authoritative."""

    scale: ScaleController = field(default_factory=ScaleController)
    last_signal: RuntimeSignal | None = None
    faults: list[str] = field(default_factory=list)

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, value))

    @staticmethod
    def _finite(value: float, name: str) -> float:
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite")
        return value

    def step(self, simulation: Simulation) -> RuntimeSignal:
        state = simulation.state
        agents = [a for a in state.agents.values() if a.health > 0.0]
        organisms = [o for o in state.ecosystem.organisms.values() if getattr(o, "alive", True)]
        species = [s for s in state.ecosystem.species.values() if getattr(s, "population", 1) > 0]
        population = len(agents) + len(organisms)
        biomass = self._finite(sum(max(0.0, float(getattr(o, "biomass", 0.0))) for o in organisms), "biomass")

        water_stress = climate_stress = 0.0
        snapshot = state.planet_snapshot
        if snapshot is not None and snapshot.cells:
            cells = [cell for row in snapshot.cells for cell in row]
            water = [self._clamp(float(cell.hydrology.groundwater_mm) / 50.0) for cell in cells]
            temperatures = [self._clamp(abs(float(cell.atmosphere.temperature_c) - 15.0) / 40.0) for cell in cells]
            water_stress = 1.0 - sum(water) / len(water)
            climate_stress = sum(temperatures) / len(temperatures)

        health_states = list(state.health.states.values())
        disease_pressure = (self._clamp(sum(1.0 - self._clamp(float(h.health)) for h in health_states) / len(health_states)) if health_states else 0.0)
        quantities = list(state.resources.quantities.values())
        resource_stress = (self._clamp(1.0 / (1.0 + sum(max(0.0, float(v)) for v in quantities) / len(quantities))) if quantities else 0.0)
        social_cohesion = (sum(self._clamp(float(a.personality.cooperation)) for a in agents) / len(agents)) if agents else 0.0
        economic_activity = (self._clamp(sum(max(0.0, float(w.balance)) for w in state.wallets.values()) / max(1.0, len(state.wallets) * 100.0)) if state.wallets else 0.0)

        signal = RuntimeSignal(simulation.time.tick, population, len(species), biomass, self._clamp(water_stress), self._clamp(climate_stress), disease_pressure, resource_stress, social_cohesion, economic_activity)
        self.last_signal = signal
        self.validate(simulation)
        return signal

    def validate(self, simulation: Simulation) -> tuple[str, ...]:
        faults: list[str] = []
        if self.last_signal is None:
            faults.append("runtime signal missing")
        elif self.last_signal.tick != simulation.time.tick:
            faults.append("runtime signal tick mismatch")
        if any(a.health < 0.0 or a.health > 1.0 for a in simulation.state.agents.values()):
            faults.append("agent health outside [0,1]")
        if any(w.balance < 0.0 for w in simulation.state.wallets.values()):
            faults.append("wallet balance below zero")
        self.faults[:] = faults
        if faults:
            raise ValueError("; ".join(faults))
        return tuple(faults)
