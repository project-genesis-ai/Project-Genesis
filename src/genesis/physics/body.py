from __future__ import annotations

from dataclasses import dataclass

from .vectors import Vec3


@dataclass(slots=True)
class Body:
    """Minimal Newtonian body state using SI units."""

    body_id: str
    mass_kg: float
    position: Vec3 = Vec3()
    velocity_mps: Vec3 = Vec3()

    def __post_init__(self) -> None:
        if not self.body_id.strip():
            raise ValueError("body_id cannot be empty")
        if self.mass_kg <= 0.0:
            raise ValueError("mass_kg must be positive")

    def integrate(self, acceleration_mps2: Vec3, dt_seconds: float) -> None:
        if dt_seconds < 0.0:
            raise ValueError("dt_seconds cannot be negative")
        self.velocity_mps = self.velocity_mps + acceleration_mps2 * dt_seconds
        self.position = self.position + self.velocity_mps * dt_seconds
