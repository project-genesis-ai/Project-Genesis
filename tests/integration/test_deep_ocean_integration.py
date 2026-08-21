from genesis.planet.coupling import PlanetEngine
from genesis.planet.ocean_depth import OceanEcosystem
from genesis.planet.terrain import TerrainParams


def test_deep_ocean_ecosystem_is_authoritative_and_persistent() -> None:
    engine = PlanetEngine(TerrainParams(width=16, height=16, seed=17))

    first = engine.step(1)
    assert first.deep_ocean
    assert all("deep" in ecosystem.layers for _, _, ecosystem in first.deep_ocean)

    key = (first.deep_ocean[0][0], first.deep_ocean[0][1])
    first_ecosystem = engine.ocean_ecosystems[key]
    first_biomass = first_ecosystem.layers["deep"].biomass

    second = engine.step(2)
    second_ecosystem = engine.ocean_ecosystems[key]

    assert second_ecosystem is first_ecosystem
    assert second_ecosystem.layers["deep"].biomass is first_biomass
    assert second.deep_ocean


def test_deep_ocean_primitive_has_three_zones_at_abyssal_depth() -> None:
    ecosystem = OceanEcosystem.create(
        surface_temperature_c=22.0,
        depth_m=4000.0,
        nutrients=1.5,
    )

    ecosystem.step()

    assert set(ecosystem.layers) == {"photic", "twilight", "deep"}
    assert ecosystem.layers["photic"].biomass.get("phytoplankton", 0.0) > 0.0
    assert ecosystem.layers["deep"].depth_min_m >= 250.0
    assert ecosystem.layers["deep"].depth_max_m == 4000.0
