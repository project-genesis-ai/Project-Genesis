from genesis.planet.atmosphere import AtmosphereEngine
from genesis.planet.ocean_depth import OceanEcosystem
from genesis.planet.weather_field import RegionalWeatherEngine


def test_weather_field_is_spatially_coupled() -> None:
    engine = RegionalWeatherEngine(AtmosphereEngine())
    snapshot = engine.step(
        width=8,
        height=6,
        tick=10,
        latitude_for_row=lambda row: -75 + row * 30,
        elevation={(x, y): float((x + y) * 10) for y in range(6) for x in range(8)},
        moisture={(x, y): 0.3 + 0.05 * ((x + y) % 3) for y in range(6) for x in range(8)},
        ocean_fraction=0.62,
    )
    assert len(snapshot.cells) == 48
    assert all(0 <= cell.state.humidity <= 1 for cell in snapshot.cells)
    assert all(0 <= cell.state.storm_intensity <= 1 for cell in snapshot.cells)


def test_deep_ocean_has_distinct_ecological_zones() -> None:
    ocean = OceanEcosystem.create(surface_temperature_c=22, depth_m=4000, nutrients=1.5)
    ocean.step()
    assert set(ocean.layers) == {"photic", "twilight", "deep"}
    assert ocean.layers["photic"].biomass.get("phytoplankton", 0) > 0
    assert ocean.layers["deep"].depth_min_m >= 250
    assert ocean.layers["deep"].biomass.get("deep_predator", 0) >= 0
