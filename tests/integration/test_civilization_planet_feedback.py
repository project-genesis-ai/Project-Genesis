from genesis.planet.civilization_feedback import EnvironmentalImpact
from genesis.planet.coupling import PlanetEngine
from genesis.planet.terrain import TerrainParams


def _deep_ocean_key(engine: PlanetEngine) -> tuple[int, int]:
    snapshot = engine.step(1)
    assert snapshot.deep_ocean
    x, y, _ = snapshot.deep_ocean[0]
    return x, y


def test_water_extraction_reduces_persistent_groundwater() -> None:
    params = TerrainParams(width=16, height=16, seed=23)
    baseline = PlanetEngine(params)
    impacted = PlanetEngine(params)

    key = _deep_ocean_key(baseline)
    impacted.step(1)
    impacted.set_civilization_impacts(
        {
            key: EnvironmentalImpact(
                population_pressure=0.2,
                agriculture_pressure=0.4,
                land_conversion=0.4,
                water_extraction=100.0,
                pollution=0.0,
            )
        }
    )

    baseline.step(2)
    impacted.step(2)

    assert impacted.hydrology_runtime.groundwater[key].storage_mm < baseline.hydrology_runtime.groundwater[key].storage_mm


def test_pollution_reaches_deep_ocean_oxygen_and_biomass() -> None:
    params = TerrainParams(width=16, height=16, seed=23)
    clean = PlanetEngine(params)
    polluted = PlanetEngine(params)

    key = _deep_ocean_key(clean)
    polluted.step(1)
    polluted.set_civilization_impacts(
        {
            key: EnvironmentalImpact(
                population_pressure=0.5,
                agriculture_pressure=0.7,
                land_conversion=0.7,
                water_extraction=0.0,
                pollution=1.0,
            )
        }
    )

    clean_snapshot = clean.step(2)
    polluted_snapshot = polluted.step(2)
    clean_cell = next(cell for x, y, cell in clean_snapshot.aquatic if (x, y) == key)
    polluted_cell = next(cell for x, y, cell in polluted_snapshot.aquatic if (x, y) == key)

    assert polluted_cell.dissolved_oxygen < clean_cell.dissolved_oxygen
    assert polluted_cell.biomass["ocean_phytoplankton"] < clean_cell.biomass["ocean_phytoplankton"]
