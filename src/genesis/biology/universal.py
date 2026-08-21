"""Universal deterministic biology primitives for all living species.

This module deliberately separates immutable simulation identity/genetics from
mutable phenotype, environment exposure, learning, and behaviour.  It is a
small shared foundation that can be used by plants, animals, microbes, and
humans without forcing identical cognition on every species.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Mapping, Sequence


NumberMap = Mapping[str, float]


def _digest(*parts: object) -> str:
    payload = "|".join(str(p) for p in parts).encode("utf-8")
    return sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class Genome:
    """Heritable genome represented as stable loci and a lineage fingerprint."""

    loci: tuple[int, ...]
    generation: int = 0
    lineage: str = "root"

    @property
    def fingerprint(self) -> str:
        return _digest(self.lineage, self.generation, *self.loci)

    @staticmethod
    def founder(seed: int, loci_count: int = 16) -> "Genome":
        if loci_count <= 0:
            raise ValueError("loci_count must be positive")
        loci = tuple(int(_digest(seed, i)[:8], 16) for i in range(loci_count))
        return Genome(loci=loci, lineage=_digest("founder", seed))

    def reproduce(self, other: "Genome", seed: int, mutation_rate: float = 0.01) -> "Genome":
        if len(self.loci) != len(other.loci):
            raise ValueError("parent genomes must have equal locus counts")
        if not 0.0 <= mutation_rate <= 1.0:
            raise ValueError("mutation_rate must be between 0 and 1")
        child = []
        for i, (a, b) in enumerate(zip(self.loci, other.loci)):
            pick = int(_digest(seed, i, a, b)[0:2], 16) & 1
            value = a if pick == 0 else b
            roll = int(_digest(seed, "mutation", i, value)[0:8], 16) / 0xFFFFFFFF
            if roll < mutation_rate:
                value ^= int(_digest(seed, "mutation-value", i)[:8], 16)
            child.append(value)
        lineage = _digest("child", self.fingerprint, other.fingerprint, seed)
        return Genome(tuple(child), max(self.generation, other.generation) + 1, lineage)


@dataclass(frozen=True, slots=True)
class IndividualIdentity:
    """Unique simulation identity; never use genome fingerprint as identity."""

    identity_id: str
    species_id: str
    birth_tick: int
    genome_fingerprint: str

    @staticmethod
    def create(species_id: str, birth_tick: int, genome: Genome, birth_event: str) -> "IndividualIdentity":
        identity = _digest("individual", species_id, birth_tick, genome.fingerprint, birth_event)
        return IndividualIdentity(identity, species_id, birth_tick, genome.fingerprint)


@dataclass(slots=True)
class EnvironmentExposure:
    """Current local environmental signals presented to an organism."""

    values: dict[str, float] = field(default_factory=dict)

    def get(self, key: str, default: float = 0.0) -> float:
        return float(self.values.get(key, default))


@dataclass(slots=True)
class InternalState:
    energy: float = 1.0
    hydration: float = 1.0
    stress: float = 0.0
    temperature_load: float = 0.0
    safety: float = 1.0

    def clamp(self) -> None:
        self.energy = min(1.0, max(0.0, self.energy))
        self.hydration = min(1.0, max(0.0, self.hydration))
        self.stress = min(1.0, max(0.0, self.stress))
        self.temperature_load = min(1.0, max(0.0, self.temperature_load))
        self.safety = min(1.0, max(0.0, self.safety))


@dataclass(frozen=True, slots=True)
class BiologicalTraits:
    metabolism: float = 0.5
    mobility: float = 0.5
    sensing: float = 0.5
    learning: float = 0.0
    sociality: float = 0.0
    cognition: float = 0.0
    fertility: float = 0.5
    resilience: float = 0.5


@dataclass(slots=True)
class BiologicalIndividual:
    identity: IndividualIdentity
    genome: Genome
    traits: BiologicalTraits
    internal: InternalState = field(default_factory=InternalState)
    memory: dict[str, float] = field(default_factory=dict)

    def perceive(self, environment: EnvironmentExposure) -> None:
        food = environment.get("food", 0.5)
        water = environment.get("water", 0.5)
        danger = environment.get("danger", 0.0)
        temperature = environment.get("temperature", 0.5)
        self.internal.energy += (food - 0.5) * 0.08 - self.traits.metabolism * 0.02
        self.internal.hydration += (water - 0.5) * 0.08
        self.internal.stress += danger * 0.08 + abs(temperature - 0.5) * 0.04
        self.internal.safety = 1.0 - danger
        self.internal.temperature_load += abs(temperature - 0.5) * 0.05
        self.internal.clamp()

    def choose_action(self, environment: EnvironmentExposure) -> str:
        """Deterministic behaviour policy; species-specific policy can extend this."""
        self.perceive(environment)
        if self.internal.hydration < 0.3:
            action = "seek_water"
        elif self.internal.energy < 0.3:
            action = "seek_food"
        elif self.internal.safety < 0.3:
            action = "seek_shelter" if self.traits.mobility >= 0.2 else "hide"
        elif self.internal.stress > 0.7:
            action = "avoid_stressor"
        elif self.traits.sociality > 0.6 and environment.get("conspecifics", 0.0) > 0.2:
            action = "socialize"
        elif self.traits.learning > 0.5:
            action = "explore"
        else:
            action = "rest"
        if self.traits.learning > 0:
            self.memory[action] = self.memory.get(action, 0.0) + self.traits.learning
        return action


@dataclass(frozen=True, slots=True)
class EcologicalInteraction:
    source_species: str
    target_species: str
    interaction: str
    strength: float


@dataclass(slots=True)
class Population:
    species_id: str
    individuals: dict[str, BiologicalIndividual] = field(default_factory=dict)
    carrying_capacity: int = 1_000

    @property
    def size(self) -> int:
        return len(self.individuals)

    def add(self, individual: BiologicalIndividual) -> None:
        if individual.identity.species_id != self.species_id:
            raise ValueError("individual species does not match population")
        if individual.identity.identity_id in self.individuals:
            raise ValueError("duplicate individual identity")
        if self.size >= self.carrying_capacity:
            raise ValueError("population carrying capacity exceeded")
        self.individuals[individual.identity.identity_id] = individual


@dataclass(frozen=True, slots=True)
class SpeciesDefinition:
    species_id: str
    kingdom: str
    traits: BiologicalTraits
    reproduction_rate: float
    mutation_rate: float
    diet: tuple[str, ...] = ()
    habitat: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.reproduction_rate <= 1.0:
            raise ValueError("reproduction_rate must be between 0 and 1")
        if not 0.0 <= self.mutation_rate <= 1.0:
            raise ValueError("mutation_rate must be between 0 and 1")


def ecological_pressure(interactions: Sequence[EcologicalInteraction], populations: Mapping[str, int]) -> dict[str, float]:
    """Aggregate deterministic pressure without owning species populations."""
    pressure: dict[str, float] = {}
    for edge in interactions:
        source = float(populations.get(edge.source_species, 0))
        target = float(populations.get(edge.target_species, 0))
        pressure[edge.target_species] = pressure.get(edge.target_species, 0.0) + source * edge.strength
        if edge.interaction in {"predation", "parasitism", "competition"}:
            pressure[edge.source_species] = pressure.get(edge.source_species, 0.0) - target * edge.strength
    return pressure
