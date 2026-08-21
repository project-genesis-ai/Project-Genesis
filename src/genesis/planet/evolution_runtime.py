from __future__ import annotations

from dataclasses import dataclass
import random

from genesis.life.organism import Organism
from genesis.life.species import Species
from .evolution import EvolutionEngine, SpeciationEvent


@dataclass(frozen=True, slots=True)
class PopulationEnvironment:
    population_size: int
    isolation: float
    environmental_distance: float
    competition: float
    generation: int


class EvolutionRuntime:
    """Turns persistent environmental isolation into actual speciation events."""

    def __init__(self, seed: int = 0) -> None:
        self.rng = random.Random(seed)
        self.engine = EvolutionEngine()

    def evaluate(self, species: Species, environment: PopulationEnvironment) -> tuple[Species, SpeciationEvent] | None:
        return self.engine.speciate(
            parent=species,
            child_species_id=f"{species.species_id}:g{environment.generation}",
            isolation=environment.isolation,
            environmental_distance=environment.environmental_distance,
            competition=environment.competition,
            generation=environment.generation,
            rng=self.rng,
        )

    def population_traits(self, organisms: tuple[Organism, ...]) -> dict[str, float]:
        if not organisms:
            return {"mean_speed": 0.0, "mean_fertility": 0.0, "mean_resistance": 0.0}
        genomes = [organism.genome for organism in organisms if organism.genome is not None]
        if not genomes:
            return {"mean_speed": 0.0, "mean_fertility": 0.0, "mean_resistance": 0.0}
        return {
            "mean_speed": sum(g.speed_mps for g in genomes) / len(genomes),
            "mean_fertility": sum(g.fertility for g in genomes) / len(genomes),
            "mean_resistance": sum(g.disease_resistance for g in genomes) / len(genomes),
        }
