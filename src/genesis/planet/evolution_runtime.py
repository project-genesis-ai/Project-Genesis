from __future__ import annotations

from dataclasses import dataclass
import random

from genesis.life.ecosystem import Ecosystem
from genesis.life.genetics import Genome
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

    def __post_init__(self) -> None:
        if self.population_size < 0 or self.generation < 0:
            raise ValueError("population_size and generation cannot be negative")
        for value in (self.isolation, self.environmental_distance, self.competition):
            if not 0.0 <= value <= 1.0:
                raise ValueError("evolution pressures must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class SpeciationApplication:
    """Immutable record of a speciation event applied to living organisms."""

    event: SpeciationEvent
    parent_population_before: int
    child_population_after: int
    reassigned_organism_ids: tuple[str, ...]


class EvolutionRuntime:
    """Turns persistent environmental isolation into deterministic population divergence."""

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
            population_size=environment.population_size,
            rng=self.rng,
        )

    def apply_speciation(
        self,
        ecosystem: Ecosystem,
        species_id: str,
        environment: PopulationEnvironment,
    ) -> SpeciationApplication | None:
        """Evaluate and apply one generation of deterministic speciation.

        A bounded minority cohort is selected from the existing population so
        speciation creates a real branching lineage instead of replacing the
        parent species wholesale. Selection is stable by fitness and organism ID;
        no hidden global randomness is used beyond this runtime's seeded RNG.
        """
        species = ecosystem.species.get(species_id)
        if species is None:
            raise KeyError(f"Unknown species: {species_id}")
        observed = tuple(
            organism for organism in ecosystem.organisms.values()
            if organism.alive and organism.species.species_id == species_id
        )
        if environment.population_size != len(observed):
            raise ValueError("population_size must equal the observed live population")
        result = self.evaluate(species, environment)
        if result is None:
            return None
        child, event = result
        if child.species_id in ecosystem.species:
            raise ValueError(f"Species already exists: {child.species_id}")

        ecosystem.register_species(child)
        if not observed:
            return None

        fraction = min(0.5, max(0.1, 0.1 + 0.4 * environment.isolation))
        cohort_size = min(child.carrying_capacity, max(1, round(len(observed) * fraction)))
        ranked = sorted(
            observed,
            key=lambda organism: (-organism.genome.fitness if organism.genome is not None else 0.0, organism.organism_id),
        )
        selected = tuple(ranked[:cohort_size])
        mutation_sigma = 0.01 + 0.06 * environment.isolation * environment.environmental_distance
        for organism in selected:
            assert organism.genome is not None
            organism.genome = Genome.inherit(organism.genome, organism.genome, self.rng, mutation_sigma=mutation_sigma)
            organism.species = child

        return SpeciationApplication(
            event=event,
            parent_population_before=len(observed),
            child_population_after=len(selected),
            reassigned_organism_ids=tuple(organism.organism_id for organism in selected),
        )

    def lineage(self, ecosystem: Ecosystem, species_id: str) -> tuple[str, ...]:
        """Return the lineage from root species to the requested species."""
        if species_id not in ecosystem.species:
            raise KeyError(f"Unknown species: {species_id}")
        chain: list[str] = []
        current = ecosystem.species[species_id]
        seen: set[str] = set()
        while current is not None:
            if current.species_id in seen:
                raise RuntimeError("species lineage cycle detected")
            seen.add(current.species_id)
            chain.append(current.species_id)
            if current.parent_species_id is None:
                break
            current = ecosystem.species.get(current.parent_species_id)
            if current is None:
                raise RuntimeError("species lineage parent is missing")
        chain.reverse()
        return tuple(chain)

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
