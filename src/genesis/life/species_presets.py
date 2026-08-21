from __future__ import annotations

from .species import Species, TrophicLevel


def forest_species() -> tuple[Species, ...]:
    """Starter forest species used by deterministic examples and tests."""
    return (
        Species("oak", "Oak", TrophicLevel.PRODUCER, 500, 5000, 0.02, 0.0),
        Species("deer", "Deer", TrophicLevel.HERBIVORE, 300, 3000, 0.01, 12.0, ("oak",)),
        Species("tiger", "Tiger", TrophicLevel.CARNIVORE, 700, 5000, 0.005, 16.0, ("deer",)),
    )
