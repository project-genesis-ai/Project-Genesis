import pytest

from genesis.core.finalization import run_final_validation


def test_final_validation_passes_for_deterministic_long_run() -> None:
    report = run_final_validation(steps=8, seed=41)

    assert report.ok
    assert report.ticks == 8
    assert report.deterministic
    assert report.invariants_ok
    assert report.hardening_ok
    assert report.checkpoint_stable
    assert report.finite_metrics
    assert report.faults == ()


def test_final_validation_rejects_non_positive_steps() -> None:
    with pytest.raises(ValueError, match="steps must be positive"):
        run_final_validation(steps=0)
