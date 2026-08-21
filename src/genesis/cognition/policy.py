from __future__ import annotations

from genesis.agents.agent import Agent
from genesis.cognition.decision import DecisionEngine, DecisionOption, DecisionResult
from genesis.world.world import WorldState


class SurvivalPolicy:
    """Builds deterministic survival choices from an agent's local state."""

    def __init__(self, decision_engine: DecisionEngine | None = None) -> None:
        self.engine = decision_engine or DecisionEngine()

    def choose(self, agent: Agent, world: WorldState) -> DecisionResult:
        options: list[DecisionOption] = []
        if agent.needs.hunger > 0.0 and agent.inventory.get("food", 0.0) >= 1.0:
            options.append(DecisionOption("eat", agent.needs.hunger, "reduce hunger"))
        if agent.needs.thirst > 0.0 and agent.inventory.get("water", 0.0) >= 1.0:
            options.append(DecisionOption("drink", agent.needs.thirst, "reduce thirst"))
        if agent.needs.energy > 0.0:
            options.append(DecisionOption("rest", agent.needs.energy, "recover energy"))
        if not options:
            options.append(DecisionOption("idle", 0.0, "no urgent local need"))
        return self.engine.choose(agent, world, options)
