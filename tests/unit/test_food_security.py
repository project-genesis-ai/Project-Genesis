from genesis.agriculture import Crop, Farm, FarmState, FoodSystem


def test_food_shortage_scales_with_population() -> None:
    food = FoodSystem(per_capita_demand=2.0, spoilage_rate=0.0)
    balance = food.step(population=10, production=12)

    assert balance.demand == 20
    assert balance.consumed == 12
    assert balance.deficit == 8
    assert balance.security == 0.6
    assert balance.starvation_pressure == 0.4
    assert balance.migration_pressure == 0.32


def test_surplus_becomes_persistent_reserve() -> None:
    food = FoodSystem(per_capita_demand=1.0, spoilage_rate=0.0)
    first = food.step(population=5, production=10)
    second = food.step(population=8, production=0)

    assert first.reserve == 5
    assert second.consumed == 5
    assert second.deficit == 3
    assert second.reserve == 0


def test_farm_harvest_is_authoritative_food_production() -> None:
    crop = Crop("wheat", "Wheat", growth_ticks=2, yield_per_area=10.0, water_need=0.5)
    farm = Farm("f1", crop, area=2.0, soil_fertility=1.0, water=1.0)
    farm.plant()
    farm.step(2)
    assert farm.state is FarmState.READY

    food = FoodSystem(spoilage_rate=0.0)
    balance = food.step_from_farms(population=10, farms=(farm,))

    assert balance.production == 20.0
    assert balance.security == 1.0
    assert farm.state is FarmState.HARVESTED


def test_ready_farm_cannot_be_counted_twice() -> None:
    crop = Crop("rice", "Rice", growth_ticks=1, yield_per_area=5.0)
    farm = Farm("f1", crop, area=1.0)
    farm.plant()
    farm.step()

    food = FoodSystem(spoilage_rate=0.0)
    first = food.step_from_farms(population=0, farms=(farm,))
    second = food.step_from_farms(population=0, farms=(farm,))

    assert first.production == 5.0
    assert second.production == 0.0
    assert second.reserve == 5.0
