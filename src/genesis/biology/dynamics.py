"""Deterministic population, migration, and host-pathogen dynamics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .universal import BiologicalIndividual, Genome, IndividualIdentity, Population


@dataclass(frozen=True, slots=True)
class MigrationDecision:
    individual_id: str
    source: str
    destination: str
    pressure: float


@dataclass(frozen=True, slots=True)
class InfectionState:
    pathogen_id: str
    host_id: str
    load: float = 0.0
    transmissibility: float = 0.1
    damage: float = 0.05


class BiologicalDynamics:
    """Stateless deterministic helpers; callers retain authoritative world state."""

    @staticmethod
    def reproduce(
        parent_a: BiologicalIndividual,
        parent_b: BiologicalIndividual,
        seed: int,
        birth_tick: int,
        species_id: str,
        birth_event: str,
        mutation_rate: float,
    ) -> BiologicalIndividual:
        if parent_a.identity.species_id != species_id or parent_b.identity.species_id != species_id:
            raise ValueError("parents must belong to the child species")
        genome = parent_a.genome.reproduce(parent_b.genome, seed, mutation_rate)
        identity = IndividualIdentity.create(species_id, birth_tick, genome, birth_event)
        return BiologicalIndividual(identity=identity, genome=genome, traits=parent_a.traits)

    @staticmethod
    def migrate(
        individual: BiologicalIndividual,
        source: str,
        candidates: Iterable[tuple[str, float]],
        threshold: float = 0.0,
    ) -> MigrationDecision | None:
        ranked = sorted(((str(destination), float(pressure)) for destination, pressure in candidates), key=lambda x: (-x[1], x[0]))
        if not ranked or ranked[0][1] <= threshold:
            return None
        destination, pressure = ranked[0]
        return MigrationDecision(individual.identity.identity_id, source, destination, pressure)

    @staticmethod
    def transmit(
        infection: InfectionState,
        susceptible_host_ids: Iterable[str],
        seed: int,
    ) -> tuple[InfectionState, ...]:
        """Deterministic transmission sample; host state remains caller-owned."""
        result: list[InfectionState] = []
        for index, host_id in enumerate(sorted(set(susceptible_host_ids))):
            token = int(__import__("hashlib").sha256(f"{seed}|{infection.pathogen_id}|{host_id}|{index}".encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
            if token < infection.transmissibility:
                result.append(InfectionState(infection.pathogen_id, host_id, infection.load * 0.5, infection.transmissibility, infection.damage))
        return tuple(result)

    @staticmethod
    def apply_infection(individual: BiologicalIndividual, infection: InfectionState) -> None:
        if infection.host_id != individual.identity.identity_id:
            raise ValueError("infection host does not match individual")
        individual.internal.energy = max(0.0, individual.internal.energy - infection.load * infection.damage)
        individual.internal.stress = min(1.0, individual.internal.stress + infection.load * infection.damage)
        individual.internal.clamp()


def population_snapshot(population: Population) -> dict[str, object]:
    """Stable serialization-ready summary for checkpoints/observability."""
    identities = sorted(population.individuals)
    return {"species_id": population.species_id, "size": population.size, "identities": identities}
