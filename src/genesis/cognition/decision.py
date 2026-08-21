from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from genesis.agents.agent import Agent
from genesis.world.world import WorldState


@dataclass(frozen=True, slots=True)
class DecisionOption:
    action_name: str
    score: float
    reason: str = ""


@dataclass(frozen=True, slots=True)
class DecisionResult:
    selected: DecisionOption | None
    considered: tuple[DecisionOption, ...]


class DecisionEngine:
    """Deterministic rule-based decision layer; LLMs can be adapters later."""

    def choose(self, agent: Agent, world: WorldState, options: Iterable[DecisionOption]) -> DecisionResult:
        ordered = tuple(sorted(options, key=lambda item: (-item.score, item.action_name)))
        return DecisionResult(ordered[0] if ordered else None, ordered)

    @staticmethod
    def need_score(value: float) -> float:
        return max(0.0, min(1.0, value))
