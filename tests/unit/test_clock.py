import pytest

from genesis.core.clock import SimulationTime


def test_clock_advances_deterministically() -> None:
    time = SimulationTime()
    assert time.advance(3).tick == 3
    assert time.tick == 0


def test_clock_rejects_negative_values() -> None:
    with pytest.raises(ValueError):
        SimulationTime(-1)
    with pytest.raises(ValueError):
        SimulationTime().advance(-1)
