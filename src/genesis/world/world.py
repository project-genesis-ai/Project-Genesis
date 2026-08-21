from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class WorldState:
    """Authoritative minimal world state. Domain systems will extend this model."""

    name: str = "Genesis"
    resources: dict[str, float] = field(default_factory=dict)

    def resource(self, name: str) -> float:
        return self.resources.get(name, 0.0)

    def set_resource(self, name: str, amount: float) -> None:
        if amount < 0:
            raise ValueError("Resource amount cannot be negative")
        self.resources[name] = amount
