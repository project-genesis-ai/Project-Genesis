from genesis.planet.civilization_feedback import EnvironmentalImpact


def test_impact_rejects_negative_extraction() -> None:
    try:
        EnvironmentalImpact(0.0, 0.0, 0.0, -1.0, 0.0)
    except ValueError:
        assert True
    else:
        assert False
