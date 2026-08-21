from __future__ import annotations

from dataclasses import dataclass

from genesis.life.ecosystem import Ecosystem
from genesis.world.environment import Environment

from .bridge import environment_exposure, interaction_edges, universal_view


@dataclass(frozen=True, slots=True)
class BiologicalAction:
    organism_id: str
    action: str
    exposure: tuple[tuple[str, float], ...]


@dataclass(frozen=True, slots=True)
class BiologicalStep:
    actions: tuple[BiologicalAction, ...]
    interactions: tuple


class UniversalBiologyRuntime:
    """Non-authoritative adapter that makes universal biology executable in LifeSystem."""

    def step(self, environment: Environment, ecosystem: Ecosystem, birth_tick: int = 0) -> BiologicalStep:
        actions: list[BiologicalAction] = []
        organisms = tuple(sorted((o for o in ecosystem.organisms.values() if o.alive), key=lambda item: item.organism_id))
        for organism in organisms:
            view = universal_view(organism, birth_tick=birth_tick)
            exposure = environment_exposure(environment, organism)
            action = view.choose_action(exposure)
            organism.memory[f"universal:{action}"] = organism.memory.get(f"universal:{action}", 0.0) + 1.0
            actions.append(BiologicalAction(organism.organism_id, action, tuple(sorted((k, float(v)) for k, v in exposure.values.items()))))
        interactions = interaction_edges(organisms)
        return BiologicalStep(tuple(actions), interactions)
