from __future__ import annotations

from dataclasses import dataclass, field
import math
import random
from typing import Iterable

from .genetics import Genome
from .organism import Organism


@dataclass(frozen=True, slots=True)
class GenomeRecord:
    organism_id: str
    species_id: str
    generation: int
    genome: Genome
    parent_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SelectionResult:
    organism_id: str
    fitness: float
    survival_probability: float
    selected: bool


@dataclass(slots=True)
class EvolutionRuntime:
    """Species-agnostic evolutionary accounting over the authoritative organisms.

    The runtime does not own organisms or populations. It records ancestry,
    computes relative fitness from heritable traits plus local pressures, and
    applies bounded survival selection. Reproduction remains owned by
    ``Organism.reproduce``/the population authority.
    """

    lineage: dict[str, GenomeRecord] = field(default_factory=dict)
    selections: list[SelectionResult] = field(default_factory=list)
    max_history: int = 100_000

    def __post_init__(self) -> None:
        if self.max_history < 1:
            raise ValueError("max_history must be positive")

    @staticmethod
    def _bounded(value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("evolution values must be finite")
        return max(0.0, min(1.0, value))

    @staticmethod
    def _trait_fitness(genome: Genome) -> float:
        return max(0.0, float(genome.fitness))

    @classmethod
    def environmental_fitness(cls, organism: Organism, pressure: float) -> float:
        """Combine heritable fitness with bounded environmental pressure."""
        pressure = cls._bounded(pressure)
        genome = organism.genome
        if genome is None:
            raise ValueError("organism must have a genome")
        health = cls._bounded(organism.health)
        energy = cls._bounded(organism.energy)
        resistance = cls._bounded(genome.disease_resistance / (1.0 + genome.disease_resistance))
        base = cls._bounded(cls._trait_fitness(genome) / (1.0 + cls._trait_fitness(genome)))
        stress_penalty = pressure * (1.0 - 0.5 * resistance)
        return cls._bounded(0.45 * base + 0.30 * health + 0.15 * energy + 0.10 * resistance - 0.35 * stress_penalty)

    def register(self, organism: Organism, parent_ids: Iterable[str] = ()) -> GenomeRecord:
        if organism.genome is None:
            raise ValueError("organism must have a genome")
        record = GenomeRecord(
            organism_id=organism.organism_id,
            species_id=organism.species.species_id,
            generation=0 if not parent_ids else max(
                (self.lineage[parent_id].generation for parent_id in parent_ids if parent_id in self.lineage),
                default=-1,
            ) + 1,
            genome=organism.genome,
            parent_ids=tuple(sorted(set(parent_ids))),
        )
        self.lineage[organism.organism_id] = record
        return record

    def register_many(self, organisms: Iterable[Organism]) -> None:
        for organism in sorted(organisms, key=lambda item: item.organism_id):
            if organism.alive:
                self.register(organism)

    def select(self, organisms: Iterable[Organism], pressures: dict[str, float], seed: int) -> tuple[SelectionResult, ...]:
        rng = random.Random(seed)
        results: list[SelectionResult] = []
        for organism in sorted((item for item in organisms if item.alive), key=lambda item: item.organism_id):
            fitness = self.environmental_fitness(organism, pressures.get(organism.species.species_id, 0.0))
            probability = self._bounded(0.20 + 0.80 * fitness)
            selected = rng.random() <= probability
            if not selected:
                organism.health = 0.0
                organism.die()
            results.append(SelectionResult(organism.organism_id, fitness, probability, selected))
        self.selections.extend(results)
        if len(self.selections) > self.max_history:
            del self.selections[: len(self.selections) - self.max_history]
        return tuple(results)

    def genome_distance(self, first_id: str, second_id: str) -> float:
        first = self.lineage[first_id].genome
        second = self.lineage[second_id].genome
        values = (
            abs(first.metabolic_rate - second.metabolic_rate) / max(first.metabolic_rate, second.metabolic_rate, 1e-9),
            abs(first.body_mass_kg - second.body_mass_kg) / max(first.body_mass_kg, second.body_mass_kg, 1e-9),
            abs(first.speed_mps - second.speed_mps) / max(first.speed_mps, second.speed_mps, 1e-9),
            abs(first.fertility - second.fertility),
            abs(first.disease_resistance - second.disease_resistance),
        )
        return sum(values) / len(values)

    def ancestry(self, organism_id: str) -> tuple[str, ...]:
        if organism_id not in self.lineage:
            return ()
        result: list[str] = []
        stack = list(self.lineage[organism_id].parent_ids)
        while stack:
            parent_id = stack.pop(0)
            if parent_id in result:
                continue
            result.append(parent_id)
            record = self.lineage.get(parent_id)
            if record is not None:
                stack.extend(record.parent_ids)
        return tuple(result)
