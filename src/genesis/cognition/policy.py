from __future__ import annotations

from genesis.cognition.decision import DecisionEngine, DecisionOption, DecisionResult
from genesis.agents.agent import Agent
from genesis.world.world import WorldState


class SurvivalPolicy:
    """Deterministic autonomous policy combining survival, growth and social goals."""

    def __init__(self, decision_engine: DecisionEngine | None = None) -> None:
        self.engine = decision_engine or DecisionEngine()

    def choose(self, agent: Agent, world: WorldState) -> DecisionResult:
        options: list[DecisionOption] = []
        if agent.needs.hunger > 0.0 and agent.inventory.get("food", 0.0) >= 1.0:
            options.append(DecisionOption("eat", agent.needs.hunger, "reduce hunger"))
        if agent.needs.thirst > 0.0 and agent.inventory.get("water", 0.0) >= 1.0:
            options.append(DecisionOption("drink", agent.needs.thirst, "reduce thirst"))

        # Rest competes with survival needs rather than overriding them.
        if agent.needs.energy > 0.0:
            options.append(DecisionOption("rest", agent.needs.energy * 0.8, "recover energy"))

        # Agents with knowledge and skills pursue learning/work instead of
        # becoming permanently trapped in idle once basic needs are satisfied.
        if agent.skills or agent.knowledge:
            options.append(DecisionOption("work", 0.25 + min(0.25, len(agent.skills) * 0.02), "apply skills and earn resources"))
            options.append(DecisionOption("learn", 0.20 + min(0.20, len(agent.knowledge) * 0.01), "increase knowledge"))

        # Cooperation is an intrinsic autonomous objective. It becomes more
        # attractive for cooperative personalities and when social need rises.
        cooperation = max(0.0, min(1.0, float(agent.personality.cooperation)))
        social_score = max(0.05, agent.needs.social * 0.5 + cooperation * 0.3)
        options.append(DecisionOption("socialize", social_score, "maintain social bonds"))

        if not options:
            options.append(DecisionOption("idle", 0.0, "no actionable goal"))
        return self.engine.choose(agent, world, options)
