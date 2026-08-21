from __future__ import annotations

from dataclasses import dataclass, field
import math
import statistics
import time
from typing import Callable, Mapping

from genesis.agents.agent import Agent
from genesis.core.checkpoint import build_checkpoint
from genesis.core.config import SimulationConfig
from genesis.core.metrics import SimulationMetrics, collect_metrics, validate_invariants
from genesis.core.scaling import PopulationScaler, RegionWork
from genesis.core.simulation import Simulation


@dataclass(frozen=True, slots=True)
class Scenario:
    """Reproducible simulation input independent of a particular run."""

    name: str
    seed: int = 2026
    steps: int = 100
    population: int = 8
    config: SimulationConfig = field(default_factory=SimulationConfig)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("scenario name must not be empty")
        if self.steps <= 0:
            raise ValueError("scenario steps must be positive")
        if self.population < 0:
            raise ValueError("scenario population cannot be negative")


@dataclass(frozen=True, slots=True)
class ExperimentResult:
    scenario: str
    seed: int
    steps: int
    elapsed_seconds: float
    metrics: SimulationMetrics
    checkpoint_digest: str
    invariant_ok: bool
    faults: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return self.invariant_ok and not self.faults and bool(self.checkpoint_digest)


@dataclass(frozen=True, slots=True)
class CalibrationResult:
    metric: str
    rmse: float
    mean_absolute_error: float
    samples: int

    @property
    def ok(self) -> bool:
        return self.samples > 0 and math.isfinite(self.rmse) and math.isfinite(self.mean_absolute_error)


def _build_simulation(scenario: Scenario) -> Simulation:
    config = SimulationConfig(
        seed=scenario.seed,
        ticks_per_step=scenario.config.ticks_per_step,
        seconds_per_tick=scenario.config.seconds_per_tick,
        hunger_per_tick=scenario.config.hunger_per_tick,
        thirst_per_tick=scenario.config.thirst_per_tick,
        energy_per_tick=scenario.config.energy_per_tick,
        social_per_tick=scenario.config.social_per_tick,
        comfort_per_tick=scenario.config.comfort_per_tick,
    )
    simulation = Simulation(config=config)
    for index in range(scenario.population):
        simulation.add_agent(
            Agent(
                agent_id=f"{scenario.name}:agent:{index}",
                name=f"{scenario.name} Agent {index}",
                wealth=100.0,
                skills={"research": 0.20 + (index % 5) * 0.01},
                world_x=index,
                world_y=index,
            )
        )
    return simulation


def run_scenario(scenario: Scenario) -> ExperimentResult:
    """Execute a scenario and return auditable final-state evidence."""
    simulation = _build_simulation(scenario)
    faults: list[str] = []
    started = time.perf_counter()
    for _ in range(scenario.steps):
        simulation.step()
        report = validate_invariants(simulation)
        if not report.ok:
            faults.extend(report.violations)
            break
    elapsed = time.perf_counter() - started
    metrics = collect_metrics(simulation)
    checkpoint = build_checkpoint(simulation)
    if not checkpoint.digest:
        faults.append("checkpoint digest is empty")
    return ExperimentResult(
        scenario=scenario.name,
        seed=scenario.seed,
        steps=scenario.steps,
        elapsed_seconds=elapsed,
        metrics=metrics,
        checkpoint_digest=checkpoint.digest,
        invariant_ok=validate_invariants(simulation).ok,
        faults=tuple(dict.fromkeys(faults)),
    )


def run_replicates(scenario: Scenario, replicates: int = 3) -> tuple[ExperimentResult, ...]:
    """Run deterministic seed-separated replicates for statistical comparison."""
    if replicates <= 0:
        raise ValueError("replicates must be positive")
    return tuple(
        run_scenario(
            Scenario(
                name=f"{scenario.name}:replicate:{index}",
                seed=scenario.seed + index,
                steps=scenario.steps,
                population=scenario.population,
                config=scenario.config,
            )
        )
        for index in range(replicates)
    )


def calibrate(metric: str, simulated: list[float], reference: list[float]) -> CalibrationResult:
    """Compute transparent calibration error; parameter fitting remains external."""
    if not metric.strip():
        raise ValueError("metric must not be empty")
    if not simulated or len(simulated) != len(reference):
        raise ValueError("simulated and reference samples must have equal non-zero length")
    errors = [float(a) - float(b) for a, b in zip(simulated, reference)]
    rmse = math.sqrt(statistics.fmean(error * error for error in errors))
    mae = statistics.fmean(abs(error) for error in errors)
    return CalibrationResult(metric=metric, rmse=rmse, mean_absolute_error=mae, samples=len(errors))


def scale_plan(population: int, scaler: PopulationScaler | None = None) -> tuple[RegionWork, ...]:
    """Produce a deterministic LOD/region plan without mutating simulation state."""
    return (scaler or PopulationScaler()).partition(population)


def benchmark(populations: tuple[int, ...] = (8, 32, 128), steps: int = 10) -> Mapping[int, ExperimentResult]:
    """Bounded performance probe used by CI and research runs."""
    if not populations or any(population < 0 for population in populations):
        raise ValueError("populations must contain non-negative values")
    if steps <= 0:
        raise ValueError("steps must be positive")
    return {
        population: run_scenario(Scenario(name=f"benchmark-{population}", population=population, steps=steps))
        for population in populations
    }
