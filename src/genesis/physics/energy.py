from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Energy:
    """Energy quantity in joules."""
    joules: float

    def __post_init__(self) -> None:
        if self.joules < 0.0:
            raise ValueError("energy cannot be negative")

    def __add__(self, other: Energy) -> Energy:
        return Energy(self.joules + other.joules)

@dataclass(frozen=True, slots=True)
class Power:
    """Power quantity in watts (joules per second)."""
    watts: float

    def __post_init__(self) -> None:
        if self.watts < 0.0:
            raise ValueError("power cannot be negative")

    def energy(self, seconds: float) -> Energy:
        if seconds < 0.0:
            raise ValueError("time cannot be negative")
        return Energy(self.watts * seconds)

@dataclass(frozen=True, slots=True)
class EnergyConversion:
    efficiency: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.efficiency <= 1.0:
            raise ValueError("efficiency must be between 0 and 1")

    def convert(self, input_energy: Energy) -> Energy:
        return Energy(input_energy.joules * self.efficiency)
