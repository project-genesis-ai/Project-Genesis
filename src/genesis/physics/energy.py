from __future__ import annotations

from dataclasses import dataclass

_KWH_JOULES = 3_600_000.0

@dataclass(frozen=True, slots=True)
class Energy:
    """Energy quantity in joules, with an exact unit conversion to kWh."""
    joules: float

    def __post_init__(self) -> None:
        if self.joules < 0.0:
            raise ValueError("energy cannot be negative")

    @property
    def kilowatt_hours(self) -> float:
        return self.joules / _KWH_JOULES

    @classmethod
    def from_kilowatt_hours(cls, value: float) -> Energy:
        if value < 0.0:
            raise ValueError("energy cannot be negative")
        return cls(value * _KWH_JOULES)

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
