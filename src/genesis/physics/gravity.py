from __future__ import annotations

from .vectors import Vec3

# SI units: m^3 kg^-1 s^-2.
G = 6.67430e-11


def gravitational_acceleration(
    source_mass_kg: float,
    source_position: Vec3,
    target_position: Vec3,
) -> Vec3:
    """Return Newtonian gravitational acceleration at target position."""
    if source_mass_kg < 0.0:
        raise ValueError("source_mass_kg cannot be negative")
    offset = source_position - target_position
    distance = offset.magnitude()
    if distance == 0.0:
        raise ValueError("gravitational acceleration is undefined at zero distance")
    return offset * (G * source_mass_kg / (distance**3))
