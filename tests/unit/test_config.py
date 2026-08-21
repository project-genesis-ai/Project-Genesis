from genesis.core.config import SimulationConfig


def test_physical_time_scale_defaults_to_one_second() -> None:
    assert SimulationConfig().seconds_per_tick == 1.0
