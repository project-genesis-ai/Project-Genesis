from genesis.physics.body import Body
from genesis.physics.vectors import Vec3
from genesis.physics.world import PhysicsWorld


def test_n_body_world_applies_equal_opposite_acceleration_direction() -> None:
    world = PhysicsWorld()
    world.add_body(Body("a", 1.0, position=Vec3(-1.0, 0.0, 0.0)))
    world.add_body(Body("b", 1.0, position=Vec3(1.0, 0.0, 0.0)))

    world.step(1.0)

    assert world.bodies["a"].velocity_mps.x > 0.0
    assert world.bodies["b"].velocity_mps.x < 0.0
