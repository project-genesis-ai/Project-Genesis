from __future__ import annotations

from genesis.cognition.decision import DecisionEngine, DecisionOption, DecisionResult
from genesis.agents.agent import Agent
from genesis.world.world import WorldState


class SurvivalPolicy:
    """Deterministic autonomous policy combining survival, growth and social goals."""

    _GENERATED_KNOWLEDGE_PREFIXES = ("education:", "terrain:", "learned:")

    def __init__(self, decision_engine: DecisionEngine | None = None) -> None:
        self.engine = decision_engine or DecisionEngine()

    def choose(self, agent: Agent, world: WorldState) -> DecisionResult:
        options: list[DecisionOption] = []
        if agent.needs.hunger > 0.0 and agent.inventory.get("food", 0.0) >= 1.0:
            options.append(DecisionOption("eat", agent.needs.hunger, "reduce hunger"))
        if agent.needs.thirst > 0.0 and agent.inventory.get("water", 0.0) >= 1.0:
            options.append(DecisionOption("drink", agent.needs.thirst, "reduce thirst"))

        if agent.needs.energy > 0.0:
            options.append(DecisionOption("rest", agent.needs.energy * 0.8, "recover energy"))

        meaningful_skills = tuple(
            skill for skill, value in agent.skills.items()
            if float(value) >= 0.2 and not skill.startswith("exploration_")
        )
        meaningful_knowledge = tuple(
            item for item in agent.knowledge
            if not item.startswith(self._GENERATED_KNOWLEDGE_PREFIXES)
        )
        if meaningful_skills:
            options.append(DecisionOption(
                "work",
                0.25 + min(0.25, len(meaningful_skills) * 0.02),
                "apply learned skills and earn resources",
            ))
        if meaningful_skills or meaningful_knowledge:
            options.append(DecisionOption(
                "learn",
                0.20 + min(0.20, len(meaningful_knowledge) * 0.01),
                "increase useful knowledge",
            ))

        cooperation = max(0.0, min(1.0, float(agent.personality.cooperation)))
        if agent.needs.social > 0.0 or cooperation >= 0.7:
            social_score = max(0.05, agent.needs.social * 0.5 + cooperation * 0.3)
            options.append(DecisionOption("socialize", social_score, "maintain social bonds"))

        if not options:
            options.append(DecisionOption("idle", 0.0, "no actionable goal"))
        return self.engine.choose(agent, world, options)
