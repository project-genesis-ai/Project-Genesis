"""Universal biology primitives and adapters for Genesis."""

from .bridge import environment_exposure, identity_for_organism, interaction_edges, universal_view
from .dynamics import BiologicalDynamics, InfectionState, MigrationDecision, population_snapshot
from .universal import (
    BiologicalIndividual,
    BiologicalTraits,
    EcologicalInteraction,
    EnvironmentExposure,
    Genome,
    IndividualIdentity,
    InternalState,
    Population,
    SpeciesDefinition,
    ecological_pressure,
)

__all__ = [
    "BiologicalDynamics",
    "BiologicalIndividual",
    "BiologicalTraits",
    "EcologicalInteraction",
    "EnvironmentExposure",
    "Genome",
    "IndividualIdentity",
    "InfectionState",
    "InternalState",
    "MigrationDecision",
    "Population",
    "SpeciesDefinition",
    "ecological_pressure",
    "environment_exposure",
    "identity_for_organism",
    "interaction_edges",
    "population_snapshot",
    "universal_view",
]
