from __future__ import annotations

from dataclasses import dataclass
import random

from genesis.life.genetics import Genome
from genesis.life.species import Species


@dataclass(frozen=True, slots=True)
class SpeciationEvent:
    parent_species_id: str
    child_species_id: str
    isolation: float
    environmental_distance: float
    competition: float
    generation: int


class EvolutionEngine:
    """Simple macro-evolution model: variation accumulates under isolation and selection."""

    def candidate_speciation(self, *, parent: Species, population_size: int, isolation: float,
                             environmental_distance: float, competition: float, generation: int) -> bool:
        if population_size < 2 or generation < 0:
            return False
        for value in (isolation, environmental_distance, competition):
            if not 0 <= value <= 1:
                raise ValueError("evolution pressures must be between 0 and 1")
        return isolation * environmental_distance * (1.0 - competition * 0.5) >= 0.42

    def speciate(self, *, parent: Species, child_species_id: str, isolation: float,
                 environmental_distance: float, competition: float, generation: int,
                 population_size: int | None = None,
                 rng: random.Random | None = None) -> tuple[Species, SpeciationEvent] | None:
        effective_population = parent.carrying_capacity if population_size is None else population_size
        if not self.candidate_speciation(
            parent=parent,
            population_size=effective_population,
            isolation=isolation,
            environmental_distance=environmental_distance,
            competition=competition,
            generation=generation,
        ):
            return None
        local_rng = rng or random.Random(0)
        child_genome = Genome.inherit(
            parent.reference_genome,
            parent.reference_genome,
            local_rng,
            mutation_sigma=0.02 + 0.08 * isolation * environmental_distance,
        )
        child = Species(
            species_id=child_species_id,
            common_name=f"{parent.common_name} derivative",
            trophic_level=parent.trophic_level,
            mature_age_ticks=parent.mature_age_ticks,
            max_age_ticks=max(parent.max_age_ticks, parent.mature_age_ticks + 1),
            reproduction_probability=min(1.0, parent.reproduction_probability * (0.95 + 0.08 * local_rng.random())),
            movement_speed_mps=max(0.0, parent.movement_speed_mps * (0.9 + 0.2 * local_rng.random())),
            food_species=parent.food_species,
            carrying_capacity=max(2, int(parent.carrying_capacity * (0.65 + 0.45 * local_rng.random()))),
            reference_genome=child_genome,
        )
        event = SpeciationEvent(parent.species_id, child_species_id, isolation, environmental_distance, competition, generation)
        return child, event
