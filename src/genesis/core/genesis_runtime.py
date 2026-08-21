from __future__ import annotations

from dataclasses import dataclass, field

from genesis.core.completion import CompletionRuntime, RuntimeSignal
from genesis.core.hardening import HardeningReport, audit_state
from genesis.core.scaling import PopulationScaler, RegionWork
from genesis.core.simulation import Simulation
from genesis.core.verification import VerificationReport, verify_simulation


@dataclass(slots=True)
class GenesisRuntime:
    """Full-system facade over the existing authoritative Simulation."""

    simulation: Simulation = field(default_factory=Simulation)
    completion: CompletionRuntime = field(default_factory=CompletionRuntime)
    scaler: PopulationScaler = field(default_factory=PopulationScaler)

    def step(self) -> RuntimeSignal:
        self.simulation.step()
        return self.completion.step(self.simulation)

    def run(self, steps: int) -> tuple[RuntimeSignal, ...]:
        if steps < 0:
            raise ValueError("steps cannot be negative")
        return tuple(self.step() for _ in range(steps))

    def scale_plan(self) -> tuple[RegionWork, ...]:
        population = len(self.simulation.state.agents) + len(self.simulation.state.ecosystem.organisms)
        return self.scaler.partition(population)

    def verify(self) -> VerificationReport:
        self.completion.step(self.simulation)
        return verify_simulation(self.simulation, self.completion)

    def hardening(self) -> HardeningReport:
        return audit_state(self.simulation)
