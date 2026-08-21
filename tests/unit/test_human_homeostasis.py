from genesis.agents.needs import Needs
from genesis.health.health import HealthState, HealthSystem


def test_needs_health_pressure_is_zero_below_threshold() -> None:
    assert Needs().health_pressure() == 0.0
    assert Needs(hunger=1.0).health_pressure() == 0.0


def test_severe_combined_needs_reduce_health() -> None:
    needs = Needs(hunger=1.0, thirst=1.0, energy=1.0, safety=1.0, social=1.0, comfort=1.0)
    state = HealthState(health=1.0, needs=needs)
    system = HealthSystem(states={"human": state})

    system.step(ticks=1, recovery_rate=0.0, need_damage_rate=0.02)

    assert state.health < 1.0
    assert state.health > 0.0


def test_need_damage_rate_is_validated() -> None:
    try:
        HealthSystem().step(need_damage_rate=-0.1)
    except ValueError:
        pass
    else:
        raise AssertionError("negative need damage rate must be rejected")
