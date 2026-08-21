from genesis.planet.atmosphere import AtmosphericState
from genesis.planet.coupling import PlanetEngine
from genesis.planet.terrain import TerrainParams
from genesis.planet.weather_field import WeatherCell, WeatherFieldSnapshot


class _StubRegionalWeather:
    def step(self, *, width, height, tick, latitude_for_row, elevation, moisture, ocean_fraction):
        state = AtmosphericState(
            temperature_c=7.0,
            pressure_kpa=101.0,
            humidity=0.9,
            wind_u_mps=2.0,
            wind_v_mps=-1.0,
            cloud_cover=0.8,
            precipitation_mm=123.0,
            storm_intensity=0.2,
        )
        cells = tuple(
            WeatherCell(x, y, state)
            for y in range(height)
            for x in range(width)
        )
        return WeatherFieldSnapshot(width, height, cells, tick)


def test_planet_engine_consumes_regional_weather_field() -> None:
    engine = PlanetEngine(TerrainParams(width=4, height=4, seed=41))
    engine.regional_weather = _StubRegionalWeather()

    snapshot = engine.step(3)

    assert snapshot.cells[0][0].atmosphere.precipitation_mm == 123.0
    assert snapshot.cells[0][0].atmosphere.humidity == 0.9
