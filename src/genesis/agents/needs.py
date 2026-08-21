from __future__ import annotations

from dataclasses import dataclass, fields


@dataclass(slots=True)
class Needs:
    """Normalized needs in [0, 1]; higher values mean greater urgency."""

    hunger: float = 0.0
    thirst: float = 0.0
    energy: float = 0.0
    safety: float = 0.0
    social: float = 0.0
    comfort: float = 0.0

    def __post_init__(self) -> None:
        for field_info in fields(self):
            value = getattr(self, field_info.name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_info.name} must be between 0 and 1")

    def highest_priority(self) -> str | None:
        values = {field_info.name: getattr(self, field_info.name) for field_info in fields(self)}
        name, value = max(values.items(), key=lambda item: item[1])
        return name if value > 0.0 else None

    def decay(self, *, hunger: float = 0.0, thirst: float = 0.0, energy: float = 0.0, safety: float = 0.0, social: float = 0.0, comfort: float = 0.0) -> None:
        for name, amount in locals().copy().items():
            if name == "self":
                continue
            if amount < 0:
                raise ValueError("need increments cannot be negative")
            setattr(self, name, min(1.0, getattr(self, name) + amount))
