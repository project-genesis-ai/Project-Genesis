import pytest

from genesis.life.ecology import EcologicalFlux, NutrientPool, SoilSystem


def test_nutrient_withdrawal_and_deposit_are_mass_conserving() -> None:
    pool = NutrientPool(nitrogen=2.0, phosphorus=1.0, carbon=3.0, water=4.0)
    pool.withdraw(nitrogen=0.5, phosphorus=0.25, carbon=1.0, water=2.0)
    pool.deposit(nitrogen=0.5, phosphorus=0.25, carbon=1.0, water=2.0)
    assert (pool.nitrogen, pool.phosphorus, pool.carbon, pool.water) == (2.0, 1.0, 3.0, 4.0)


def test_soil_decomposition_recycles_only_requested_fraction() -> None:
    soil = SoilSystem()
    soil.register("valley", NutrientPool())
    soil.add_litter("valley", EcologicalFlux(nitrogen=2.0, phosphorus=1.0, carbon=4.0, water=2.0))
    released = soil.decompose("valley", fraction=0.25)
    assert released == EcologicalFlux(0.5, 0.25, 1.0, 0.5)
    assert soil.litter["valley"] == EcologicalFlux(1.5, 0.75, 3.0, 1.5)
    pool = soil.pools["valley"]
    assert (pool.nitrogen, pool.phosphorus, pool.carbon, pool.water) == (1.5, 1.25, 2.0, 1.5)


def test_invalid_soil_operations_are_rejected() -> None:
    with pytest.raises(ValueError):
        NutrientPool(nitrogen=-1.0)
    soil = SoilSystem()
    soil.register("x")
    with pytest.raises(ValueError):
        soil.decompose("x", fraction=1.1)
    with pytest.raises(KeyError):
        soil.add_litter("missing", EcologicalFlux(carbon=1.0))
