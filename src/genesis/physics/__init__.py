"""Deterministic physical models used by Genesis."""

from .gravity import G, gravitational_acceleration
from .vectors import Vec3

__all__ = ["G", "Vec3", "gravitational_acceleration"]
