from __future__ import annotations

from dataclasses import dataclass, field

from .body import Body
from .gravity import gravitational_acceleration
from .vectors import Vec3


@dataclass(slots=True)
class PhysicsWorld:
    """Small deterministic N-body world using pairwise Newtonian gravity."""

    bodies: dict[str, Body] = field(default_factory=dict)

    def add_body(self, body: Body) -> None:
        if body.body_id in self.bodies:
            raise ValueError(f"Body already exists: {body.body_id}")
        self.bodies[body.body_id] = body

    def step(self, dt_seconds: float) -> None:
        if dt_seconds < 0.0:
            raise ValueError("dt_seconds cannot be negative")
        snapshot = tuple(self.bodies.values())
        accelerations: dict[str, Vec3] = {body.body_id: Vec3() for body in snapshot}
        for index, target in enumerate(snapshot):
            acceleration = Vec3()
            for source_index, source in enumerate(snapshot):
                if index == source_index:
                    continue
                acceleration = acceleration + gravitational_acceleration(
                    source.mass_kg, source.position, target.position
                )
            accelerations[target.body_id] = acceleration
        for body in snapshot:
            body.integrate(accelerations[body.body_id], dt_seconds)
