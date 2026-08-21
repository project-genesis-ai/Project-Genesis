from __future__ import annotations

from dataclasses import dataclass, field

from genesis.core.completion import CompletionRuntime, RuntimeSignal
from genesis.core.finalization import FinalValidationReport, run_final_validation
from genesis.core.hardening import HardeningReport, audit_state
from genesis.core.scaling import PopulationScaler, RegionWork
from genesis.core.simulation import Simulation
from genesis.core.verification import VerificationReport, verify_simulation
from genesis.world.emergence import EmergenceRuntime, EmergenceTransition
from genesis.civilization.emergence import CivilizationEmergenceRuntime, CivilizationTransition


@dataclass(slots=True)
class GenesisRuntime:
    """Single facade over the existing authoritative simulation."""
    simulation: Simulation = field(default_factory=Simulation)
    completion: CompletionRuntime = field(default_factory=CompletionRuntime)
    scaler: PopulationScaler = field(default_factory=PopulationScaler)
    emergence: EmergenceRuntime = field(default_factory=EmergenceRuntime)
    civilization_emergence: CivilizationEmergenceRuntime = field(default_factory=CivilizationEmergenceRuntime)

    def step(self) -> RuntimeSignal:
        self.simulation.step()
        signal = self.completion.step(self.simulation)
        self.emergence.step(self.simulation.state, self.simulation.time.tick)
        self.civilization_emergence.step(self.simulation.state, self.simulation.time.tick)
        return signal

    def run(self, steps: int) -> tuple[RuntimeSignal, ...]:
        if steps < 0:
            raise ValueError("steps cannot be negative")
        return tuple(self.step() for _ in range(steps))

    def population(self) -> int:
        return sum(1 for agent in self.simulation.state.agents.values() if agent.health > 0.0) + sum(1 for organism in self.simulation.state.ecosystem.organisms.values() if getattr(organism, "alive", True))

    def scale_plan(self) -> tuple[RegionWork, ...]:
        return self.scaler.partition(self.population())

    def emergence_signal(self):
        if self.emergence.last_signal is None:
            self.emergence.signal(self.simulation.state, self.simulation.time.tick)
        return self.emergence.last_signal

    def last_emergence_transition(self) -> EmergenceTransition | None:
        return self.emergence.transitions[-1] if self.emergence.transitions else None

    def civilization_transitions(self) -> tuple[CivilizationTransition, ...]:
        return tuple(self.civilization_emergence.transitions)

    def final_validate(self, *, steps: int = 100, seed: int = 2026) -> FinalValidationReport:
        return run_final_validation(steps=steps, seed=seed)

    def verify(self, determinism_steps: int = 1) -> VerificationReport:
        if determinism_steps < 0:
            raise ValueError("determinism_steps cannot be negative")
        self.completion.step(self.simulation)
        self.emergence.step(self.simulation.state, self.simulation.time.tick)
        self.civilization_emergence.step(self.simulation.state, self.simulation.time.tick)
        report = verify_simulation(self.simulation, self.completion, determinism_steps=determinism_steps)
        hardening = self.hardening()
        if not hardening.ok:
            report = VerificationReport(report.tick, report.checkpoint_digest, report.deterministic, False, tuple(dict.fromkeys(report.faults + hardening.faults)))
        return report

    def hardening(self) -> HardeningReport:
        return audit_state(self.simulation)
