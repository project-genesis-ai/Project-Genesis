from genesis.agriculture import Crop, Farm, FarmState
from genesis.culture import Language
from genesis.settlement import Building, BuildingType, Settlement, SettlementType


def test_language_teaching_and_speaking() -> None:
    language = Language("common")
    language.add_speaker("teacher")
    language.teach("teacher", "learner", "water", "liquid")
    assert language.speak("learner", ("water", "unknown")) == ("water",)


def test_settlement_upgrades_with_population() -> None:
    settlement = Settlement("s1", "Genesis", SettlementType.CAMP)
    settlement.add_building(Building("h1", BuildingType.HOME, capacity=2))
    for index in range(10):
        settlement.add_resident(f"a{index}")
    assert settlement.auto_upgrade()
    assert settlement.kind is SettlementType.VILLAGE


def test_farm_grows_and_harvests() -> None:
    crop = Crop("wheat", "Wheat", growth_ticks=10, yield_per_area=2.0)
    farm = Farm("f1", crop, area=5.0)
    farm.plant()
    farm.step(10, rainfall=1.0)
    assert farm.state is FarmState.READY
    assert farm.harvest() > 0
