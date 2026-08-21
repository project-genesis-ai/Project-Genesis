from genesis.planet.coupling import PlanetEngine
from genesis.planet.terrain import TerrainParams


def test_planetary_feedback_is_present_and_finite():
    engine = PlanetEngine(TerrainParams(width=8, height=6, seed=19))
    snapshot = engine.step(0)
    feedback = snapshot.feedback
    assert feedback is not None
    assert 0.0 <= feedback.ocean_fraction <= 1.0
    assert feedback.rainfall_mm >= 0.0
    assert feedback.evaporation_mm >= 0.0
    assert feedback.groundwater_mm >= 0.0
    assert feedback.water_balance_error_mm < 1e-9


def test_planetary_water_feedback_is_deterministic_across_ticks():
    left = PlanetEngine(TerrainParams(width=8, height=6, seed=23))
    right = PlanetEngine(TerrainParams(width=8, height=6, seed=23))
    for tick in (0, 1, 2):
        a = left.step(tick)
        b = right.step(tick)
        assert a.feedback == b.feedback
        assert a.rivers == b.rivers


def test_previous_water_state_feeds_back_into_weather_moisture():
    engine = PlanetEngine(TerrainParams(width=8, height=6, seed=31))
    first = engine.step(0)
    second = engine.step(1)
    assert first.feedback is not None and second.feedback is not None
    assert second.cells != first.cells
