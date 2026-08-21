from __future__ import annotations

from dataclasses import dataclass, fields


@dataclass(frozen=True, slots=True)
class Personality:
    """Stable behavioral tendencies represented as normalized traits."""

    curiosity: float = 0.5
    risk_tolerance: float = 0.5
    cooperation: float = 0.5
    patience: float = 0.5

    def __post_init__(self) -> None:
        for field_info in fields(self):
            value = getattr(self, field_info.name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_info.name} must be between 0 and 1")
