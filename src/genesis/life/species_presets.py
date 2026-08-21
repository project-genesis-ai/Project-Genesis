from __future__ import annotations

from .genetics import Genome
from .species import Species, TrophicLevel


def forest_species() -> tuple[Species, ...]:
    """Starter forest species with approximate biological reference traits."""
    return (
        Species("oak", "Oak", TrophicLevel.PRODUCER, 500, 5000, 0.02, 0.0, reference_genome=Genome(body_mass_kg=500.0, speed_mps=0.0, metabolic_rate=0.3)),
        Species("deer", "Deer", TrophicLevel.HERBIVORE, 300, 3000, 0.01, 12.0, ("oak",), reference_genome=Genome(body_mass_kg=70.0, speed_mps=12.0, fertility=1.1)),
        Species("tiger", "Tiger", TrophicLevel.CARNIVORE, 700, 5000, 0.005, 16.0, ("deer",), reference_genome=Genome(body_mass_kg=180.0, speed_mps=16.0, fertility=0.7, disease_resistance=1.2)),
    )
