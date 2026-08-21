from __future__ import annotations

from dataclasses import dataclass

from .genetics import Genome


@dataclass(frozen=True, slots=True)
class EnvironmentalPressure:
    food_scarcity: float = 0.0
    predation: float = 0.0
    disease: float = 0.0
    temperature_stress: float = 0.0
    water_scarcity: float = 0.0

    def __post_init__(self) -> None:
        values = (self.food_scarcity, self.predation, self.disease, self.temperature_stress, self.water_scarcity)
        if any(not 0.0 <= value <= 1.0 for value in values):
            raise ValueError("environmental pressures must be between 0 and 1")

    @property
    def total(self) -> float:
        return sum((self.food_scarcity, self.predation, self.disease, self.temperature_stress, self.water_scarcity)) / 5.0


def adaptive_fitness(genome: Genome, pressure: EnvironmentalPressure) -> float:
    """Relative fitness pressure; evolution changes populations over generations."""
    base = genome.fitness
    resistance = 0.5 * genome.disease_resistance
    mobility = 0.25 * genome.speed_mps
    metabolic_penalty = pressure.food_scarcity * genome.metabolic_rate
    return max(0.0, base + resistance + mobility - metabolic_penalty - pressure.total)
