"""Adapters from the existing authoritative life runtime to universal biology.

The bridge intentionally does not own organisms, populations, genetics, or
planet state. Existing LifeSystem/Ecosystem remain authoritative; this layer
provides a common identity/environment/behavior view for every species.
"""
from __future__ import annotations

from hashlib import sha256

from genesis.life.organism import Organism
from genesis.world.environment import Environment

from .universal import (
    BiologicalIndividual,
    BiologicalTraits,
    EcologicalInteraction,
    EnvironmentExposure,
    Genome,
    IndividualIdentity,
)


def identity_for_organism(organism: Organism, birth_tick: int = 0) -> IndividualIdentity:
    """Create a stable simulation identity from the authoritative organism record."""
    genome = organism.genome
    if genome is None:
        raise ValueError("organism must have a genome")
    fingerprint = sha256(repr(genome).encode("utf-8")).hexdigest()
    seed = int(fingerprint[:16], 16)
    return IndividualIdentity.create(organism.species.species_id, birth_tick, Genome.founder(seed), organism.organism_id)


def environment_exposure(environment: Environment, organism: Organism) -> EnvironmentExposure:
    """Project the organism's current habitat into generic biological signals."""
    if not environment.cells:
        return EnvironmentExposure()
    x, y = round(organism.position.x), round(organism.position.z)
    cell = min(environment.cells.values(), key=lambda c: ((c.x - x) ** 2 + (c.y - y) ** 2, c.cell_id))
    return EnvironmentExposure(
        {
            "temperature": min(1.0, max(0.0, (cell.temperature_c + 50.0) / 100.0)),
            "water": min(1.0, max(0.0, cell.water_mm / 100.0)),
            "food": min(1.0, max(0.0, cell.vegetation)),
            "danger": min(1.0, max(0.0, cell.fire_risk if hasattr(cell, "fire_risk") else 0.0)),
        }
    )


def universal_view(organism: Organism, birth_tick: int = 0) -> BiologicalIndividual:
    """Return a non-authoritative universal biological view of an organism."""
    identity = identity_for_organism(organism, birth_tick)
    genome = Genome.founder(int(identity.genome_fingerprint[:8], 16))
    traits = BiologicalTraits(
        metabolism=min(1.0, max(0.0, genome.loci[0] / 0xFFFFFFFF)),
        mobility=min(1.0, max(0.0, organism.species.migration_profile.maximum_daily_distance_km / 100.0)) if organism.species.migration_profile else 0.1,
        sensing=0.5,
        learning=0.2,
        sociality=0.0,
        cognition=0.0,
        fertility=min(1.0, max(0.0, genome.loci[1] / 0xFFFFFFFF)),
        resilience=min(1.0, max(0.0, genome.loci[2] / 0xFFFFFFFF)),
    )
    view = BiologicalIndividual(identity, genome, traits)
    view.internal.energy = organism.energy
    view.internal.safety = organism.health
    view.memory.update(organism.memory)
    return view


def interaction_edges(organisms: tuple[Organism, ...]) -> tuple[EcologicalInteraction, ...]:
    """Derive deterministic food-web interaction edges from authoritative species."""
    edges: list[EcologicalInteraction] = []
    for species in sorted({o.species for o in organisms if o.alive}, key=lambda s: s.species_id):
        for prey in sorted(species.food_species):
            edges.append(EcologicalInteraction(species.species_id, prey, "predation", 1.0))
    return tuple(edges)
