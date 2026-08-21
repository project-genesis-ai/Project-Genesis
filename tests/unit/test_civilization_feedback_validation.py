import pytest

from genesis.planet.civilization_feedback import PlanetaryCivilizationFeedback


def test_natural_land_area_must_be_positive() -> None:
    with pytest.raises(ValueError):
        PlanetaryCivilizationFeedback().assess(
            region_id="x",
            population=1,
            farmland_area=1,
            water_extraction=0,
            pollution=0,
            natural_land_area=0,
        )


def test_climate_pressure_is_bounded() -> None:
    feedback = PlanetaryCivilizationFeedback()
    feedback.assess(
        region_id="x",
        population=100_000,
        farmland_area=1000,
        water_extraction=2,
        pollution=3,
        natural_land_area=10,
    )
    assert 0 <= feedback.climate_pressure("x") <= 1
