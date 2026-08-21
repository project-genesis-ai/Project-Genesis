from math import isclose

import pytest

from genesis.physics.body import Body
from genesis.physics.gravity import G, gravitational_acceleration
from genesis.physics.vectors import Vec3


def test_vec3_operations_and_normalization() -> None:
    vector = Vec3(3.0, 4.0, 0.0)
    assert isclose(vector.magnitude(), 5.0, rel_tol=1e-12)
    normalized = vector.normalized()
    assert isclose(normalized.x, 0.6, rel_tol=1e-12)
    assert isclose(normalized.y, 0.8, rel_tol=1e-12)
    assert isclose(normalized.z, 0.0, abs_tol=1e-15)
    assert vector + Vec3(1.0, 0.0, 2.0) == Vec3(4.0, 4.0, 2.0)


def test_gravity_matches_inverse_square_law() -> None:
    acceleration = gravitational_acceleration(1.0, Vec3(), Vec3(1.0, 0.0, 0.0))
    assert isclose(acceleration.x, -G, rel_tol=1e-12)
    assert acceleration.y == 0.0


def test_gravity_rejects_zero_distance() -> None:
    with pytest.raises(ValueError):
        gravitational_acceleration(1.0, Vec3(), Vec3())


def test_body_integration_uses_si_units() -> None:
    body = Body("body", 1.0, velocity_mps=Vec3(2.0, 0.0, 0.0))
    body.integrate(Vec3(1.0, 0.0, 0.0), 2.0)
    assert body.velocity_mps == Vec3(4.0, 0.0, 0.0)
    assert body.position == Vec3(8.0, 0.0, 0.0)
