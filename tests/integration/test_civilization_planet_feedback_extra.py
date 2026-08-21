from genesis.planet.civilization_feedback import EnvironmentalImpact


def test_environmental_impact_rejects_negative_values() -> None:
    try:
        EnvironmentalImpact(0.0, 0.0, 0.0, -1.0, 0.0)
    except ValueError:
        return
    raise AssertionError("negative water extraction must be rejected")
