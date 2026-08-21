from __future__ import annotations

from dataclasses import dataclass
import time

from genesis.agents.agent import Agent
from genesis.core.checkpoint import build_checkpoint
from genesis.core.config import SimulationConfig
from genesis.core.hardening import audit_state
from genesis.core.metrics import collect_metrics
from genesis.core.simulation import Simulation
from genesis.core.verification import verify_determinism


@dataclass(frozen=True, slots=True)
class FinalValidationReport:
    """Production acceptance result for a deterministic long-run Genesis probe."""

    steps: int
    ticks: int
    deterministic: bool
    invariants_ok: bool
    hardening_ok: bool
    checkpoint_stable: bool
    finite_metrics: bool
    elapsed_seconds: float
    final_population: int
    final_wealth: float
    faults: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return all((
            self.steps > 0,
            self.ticks > 0,
            self.deterministic,
            self.invariants_ok,
            self.hardening_ok,
            self.checkpoint_stable,
            self.finite_metrics,
        ))


def _seeded_simulation(seed: int) -> Simulation:
    simulation = Simulation(config=SimulationConfig(seed=seed))
    for index in range(8):
        simulation.add_agent(
            Agent(
                agent_id=f"final-agent-{index}",
                name=f"Final Agent {index}",
                wealth=100.0 + index,
                skills={"research": 0.2 + index * 0.01, "engineering": 0.1},
                world_x=index,
                world_y=index,
            )
        )
    return simulation


def run_final_validation(*, steps: int = 100, seed: int = 2026) -> FinalValidationReport:
    """Run bounded long-horizon validation without modifying caller-owned state."""
    if steps <= 0:
        raise ValueError("steps must be positive")

    faults: list[str] = []
    start = time.perf_counter()
    simulation = _seeded_simulation(seed)
    checkpoints: list[str] = []

    for _ in range(steps):
        simulation.step()
        invariant = simulation.validate()
        if not invariant.ok:
            faults.extend(invariant.violations)
            break
        hardening = audit_state(simulation)
        if not hardening.ok:
            faults.extend(hardening.faults)
            break
        checkpoints.append(build_checkpoint(simulation).digest)

    metrics = collect_metrics(simulation)
    finite_metrics = all(
        __import__("math").isfinite(float(value))
        for value in (metrics.average_health, metrics.total_wealth)
    )
    if not finite_metrics:
        faults.append("final metrics contain non-finite values")

    checkpoint_stable = bool(checkpoints) and checkpoints[-1] == build_checkpoint(simulation).digest
    if not checkpoint_stable:
        faults.append("final checkpoint digest is not stable")

    deterministic = verify_determinism(lambda: _seeded_simulation(seed), steps=steps)
    if not deterministic:
        faults.append("independent long-run twin simulations diverged")

    elapsed = time.perf_counter() - start
    return FinalValidationReport(
        steps=steps,
        ticks=simulation.time.tick,
        deterministic=deterministic,
        invariants_ok=not faults and simulation.validate().ok,
        hardening_ok=audit_state(simulation).ok,
        checkpoint_stable=checkpoint_stable,
        finite_metrics=finite_metrics,
        elapsed_seconds=elapsed,
        final_population=metrics.living_population,
        final_wealth=metrics.total_wealth,
        faults=tuple(dict.fromkeys(faults)),
    )
