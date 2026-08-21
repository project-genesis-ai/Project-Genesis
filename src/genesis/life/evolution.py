from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import math
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
    """Species-agnostic evolutionary accounting over authoritative organisms."""

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
        parents = tuple(sorted(set(parent_ids)))
        generation = max((self.lineage[parent].generation for parent in parents if parent in self.lineage), default=-1) + 1
        record = GenomeRecord(organism.organism_id, organism.species.species_id, generation, organism.genome, parents)
        self.lineage[organism.organism_id] = record
        return record

    def register_many(self, organisms: Iterable[Organism]) -> None:
        for organism in sorted(organisms, key=lambda item: item.organism_id):
            if organism.alive and organism.organism_id not in self.lineage:
                self.register(organism)

    def evaluate(self, organisms: Iterable[Organism], pressures: dict[str, float], seed: int) -> tuple[SelectionResult, ...]:
        """Evaluate deterministic selection without mutating authoritative life state."""
        results: list[SelectionResult] = []
        for organism in sorted((item for item in organisms if item.alive), key=lambda item: item.organism_id):
            fitness = self.environmental_fitness(organism, pressures.get(organism.species.species_id, 0.0))
            probability = self._bounded(0.20 + 0.80 * fitness)
            digest = hashlib.sha256(f"selection|{seed}|{organism.organism_id}".encode("utf-8")).hexdigest()
            roll = int(digest[:16], 16) / 0xFFFFFFFFFFFFFFFF
            results.append(SelectionResult(organism.organism_id, fitness, probability, roll <= probability))
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
        queue = list(self.lineage[organism_id].parent_ids)
        while queue:
            parent_id = queue.pop(0)
            if parent_id in result:
                continue
            result.append(parent_id)
            record = self.lineage.get(parent_id)
            if record is not None:
                queue.extend(record.parent_ids)
        return tuple(result)
