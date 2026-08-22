# Phase 18 — Scale & Scientific Finalization

Phase 18 closes the engineering loop around the deterministic Genesis core. It adds an explicit experiment layer rather than embedding research orchestration inside `Simulation`.

## Scenario contract

A `Scenario` fixes a name, seed, population, horizon and simulation configuration. `run_scenario()` creates a fresh authoritative `Simulation`, executes the requested horizon, validates invariants after each step, and returns metrics plus a canonical checkpoint digest.

## Replicates

`run_replicates()` produces seed-separated, independently constructed runs. This makes cross-seed variation measurable while preserving deterministic replay for every individual seed.

## Calibration

`calibrate()` reports RMSE and mean absolute error between simulation output and reference observations. It deliberately does not silently alter parameters: calibration data and parameter fitting are research decisions and must remain auditable.

## Scaling

The existing `PopulationScaler` remains a planning/LOD authority. `scale_plan()` exposes it to experiment tooling without mutating simulation state. The individual/hybrid/aggregate thresholds are explicit and deterministic.

## Performance

`benchmark()` provides a bounded CI-safe performance probe. Larger population campaigns should run as external research jobs and consume the same scenario API. The core simulation remains deterministic and does not require a network service.

## Acceptance boundary

A green Phase 18 CI proves the experiment framework itself is deterministic, invariant-safe, finite, reproducible, and compatible with the existing scale planner. It does not claim that Earth calibration is complete without reference datasets. Scientific calibration remains an evidence-driven process, not a percentage checkbox.
