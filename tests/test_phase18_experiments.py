import math

import pytest

from genesis.core.experiments import Scenario, benchmark, calibrate, run_replicates, run_scenario, scale_plan


def test_scenario_is_reproducible() -> None:
    scenario = Scenario(name="repro", seed=77, population=3, steps=4)
    first = run_scenario(scenario)
    second = run_scenario(scenario)

    assert first.ok
    assert second.ok
    assert first.checkpoint_digest == second.checkpoint_digest
    assert first.metrics == second.metrics


def test_replicates_use_distinct_deterministic_seeds() -> None:
    results = run_replicates(Scenario(name="rep", seed=10, population=2, steps=2), replicates=3)

    assert len(results) == 3
    assert [result.seed for result in results] == [10, 11, 12]
    assert all(result.ok for result in results)


def test_calibration_is_transparent_and_finite() -> None:
    result = calibrate("population", [10, 12, 14], [9, 13, 15])

    assert result.ok
    assert result.samples == 3
    assert math.isclose(result.rmse, math.sqrt(2 / 3), rel_tol=1e-9)
    assert math.isclose(result.mean_absolute_error, 1.0)


def test_scale_plan_has_no_overlap_and_covers_population() -> None:
    plan = scale_plan(250_001)

    assert sum(region.population for region in plan) == 250_001
    assert len(plan) == 3
    assert all(region.detail == "hybrid" and region.lod == 1 for region in plan)


def test_benchmark_is_bounded() -> None:
    results = benchmark((0, 2), steps=1)

    assert set(results) == {0, 2}
    assert all(result.ok for result in results.values())


def test_invalid_experiment_inputs_are_rejected() -> None:
    with pytest.raises(ValueError):
        Scenario(name="", steps=1)
    with pytest.raises(ValueError):
        calibrate("x", [], [])
    with pytest.raises(ValueError):
        benchmark((1,), steps=0)
