from genesis.agriculture.farming import Crop, Farm
from genesis.planet.civilization_feedback import PlanetaryCivilizationFeedback


def test_civilization_pressure_is_quantified() -> None:
    feedback = PlanetaryCivilizationFeedback()
    impact = feedback.assess(
        region_id="river-valley",
        population=1000,
        farmland_area=40,
        water_extraction=0.4,
        pollution=0.2,
        natural_land_area=100,
    )
    assert impact.land_conversion == 0.4
    assert 0 <= feedback.climate_pressure("river-valley") <= 1


def test_farm_area_contributes_to_environmental_pressure() -> None:
    crop = Crop("wheat", "Wheat", growth_ticks=10, yield_per_area=2.0)
    farms = (Farm("f1", crop, area=5), Farm("f2", crop, area=8))
    assert PlanetaryCivilizationFeedback.farm_pressure(farms) == 13
