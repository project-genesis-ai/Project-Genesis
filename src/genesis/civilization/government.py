from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Government:
    government_id: str
    name: str
    population: set[str] = field(default_factory=set)
    laws: dict[str, float] = field(default_factory=dict)
    treasury: float = 0.0

    def collect_tax(self, amount: float) -> None:
        if amount < 0:
            raise ValueError("tax cannot be negative")
        self.treasury += amount
