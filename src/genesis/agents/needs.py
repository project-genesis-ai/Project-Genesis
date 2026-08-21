from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Needs:
    """Normalized agent needs in the range [0, 1]. Higher means more urgent."""

    hunger: float = 0.0
    thirst: float = 0.0
    energy: float = 0.0

    def __post_init__(self) -> None:
        for name, value in self.__dict__.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")

    def highest_priority(self) -> str | None:
        values = {"hunger": self.hunger, "thirst": self.thirst, "energy": self.energy}
        name, value = max(values.items(), key=lambda item: item[1])
        return name if value > 0.0 else None
