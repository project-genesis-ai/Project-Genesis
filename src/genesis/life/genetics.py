from __future__ import annotations

from dataclasses import dataclass
import random


@dataclass(frozen=True, slots=True)
class Genome:
    """Heritable quantitative traits with deterministic bounded mutation."""

    metabolic_rate: float = 1.0
    body_mass_kg: float = 1.0
    speed_mps: float = 1.0
    fertility: float = 1.0
    disease_resistance: float = 1.0

    def __post_init__(self) -> None:
        if self.body_mass_kg <= 0 or self.speed_mps < 0 or self.metabolic_rate <= 0:
            raise ValueError("genome physical traits must be positive")
        if self.fertility < 0 or self.disease_resistance < 0:
            raise ValueError("fitness traits cannot be negative")

    @property
    def fitness(self) -> float:
        """Composite relative fitness used only for density-selection pressure."""
        return (self.fertility * self.disease_resistance * (1.0 + self.speed_mps)) / (
            self.metabolic_rate * self.body_mass_kg
        )

    @staticmethod
    def inherit(a: Genome, b: Genome, rng: random.Random, mutation_sigma: float = 0.02) -> Genome:
        if mutation_sigma < 0:
            raise ValueError("mutation_sigma cannot be negative")

        def blend(x: float, y: float, minimum: float = 0.0) -> float:
            value = (x + y) * 0.5 + rng.gauss(0.0, mutation_sigma)
            return max(minimum, value)

        return Genome(
            metabolic_rate=blend(a.metabolic_rate, b.metabolic_rate, 0.001),
            body_mass_kg=blend(a.body_mass_kg, b.body_mass_kg, 0.001),
            speed_mps=blend(a.speed_mps, b.speed_mps),
            fertility=blend(a.fertility, b.fertility),
            disease_resistance=blend(a.disease_resistance, b.disease_resistance),
        )
