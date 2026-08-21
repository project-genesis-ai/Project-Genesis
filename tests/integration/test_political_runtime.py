from genesis.core.simulation import Simulation
from genesis.politics import Treaty


def test_treaty_expires_from_authoritative_simulation_clock() -> None:
    simulation = Simulation()
    simulation.state.politics.sign_treaty(Treaty("t1", ("a", "b"), ("peace",), 1))

    simulation.step()

    assert "t1" not in simulation.state.politics.treaties
    assert any(event.event_type == "TreatyExpired" for event in simulation.state.history.all())
    assert simulation.validate().ok


def test_conflict_intensity_decays_deterministically() -> None:
    simulation = Simulation()
    simulation.state.politics.set_conflict("a", "b", 0.5)

    simulation.step()

    assert simulation.state.politics.conflicts[("a", "b")] == 0.48
    assert simulation.validate().ok
