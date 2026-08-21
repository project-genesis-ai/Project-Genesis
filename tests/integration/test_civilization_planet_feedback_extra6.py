from genesis.planet.civilization_feedback import EnvironmentalImpact


def test_negative_environmental_impact_is_rejected() -> None:
    try:
        EnvironmentalImpact(0.0, 0.0, 0.0, -1.0, 0.0)
    except ValueError:
        return
    raise AssertionError("negative environmental impact must be rejected")
