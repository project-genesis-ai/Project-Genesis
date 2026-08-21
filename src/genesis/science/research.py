from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from genesis.civilization.innovation import Innovation

if TYPE_CHECKING:
    from genesis.core.state import SimulationState


@dataclass(slots=True)
class ResearchProject:
    project_id: str
    technology_id: str
    progress: float = 0.0
    researchers: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.project_id.strip() or not self.technology_id.strip() or not 0.0 <= self.progress <= 1.0:
            raise ValueError("invalid research project")


@dataclass(slots=True)
class ResearchSystem:
    """Deterministic science loop: researchers -> technology -> innovation -> adoption."""

    projects: dict[str, ResearchProject] = field(default_factory=dict)
    completed: list[str] = field(default_factory=list)

    def _researchers(self, state: SimulationState) -> tuple[str, ...]:
        candidates: list[str] = []
        for agent_id, agent in state.agents.items():
            person = state.demography.people.get(agent_id)
            if person is None or not person.alive or agent.health <= 0.0:
                continue
            science = max(agent.skills.get("research", 0.0), agent.skills.get("science", 0.0), agent.skills.get("engineering", 0.0))
            if science > 0.0 or "education:science" in agent.knowledge:
                candidates.append(agent_id)
        if candidates:
            return tuple(sorted(candidates))
        fallback = [
            agent_id
            for agent_id, agent in state.agents.items()
            if state.demography.people.get(agent_id) is not None
            and state.demography.people[agent_id].alive
            and agent.health > 0.0
        ]
        return tuple(sorted(fallback))

    def _known(self, state: SimulationState) -> set[str]:
        known = {technology_id for technology_id, technology in state.technologies.items() if technology.unlocked}
        for agent in state.agents.values():
            known.update(agent.knowledge)
        return known

    def researchers_for(self, technology_id: str) -> tuple[str, ...]:
        """Return the deterministic research team for one technology."""
        project = self.projects.get(f"research:{technology_id}")
        if project is None:
            return ()
        return tuple(sorted(project.researchers))

    def step(self, state: SimulationState, ticks: int) -> tuple[str, ...]:
        if ticks < 0:
            raise ValueError("ticks cannot be negative")
        researchers = self._researchers(state)
        if not researchers or not state.technologies:
            return ()
        known = self._known(state)
        unlocked_now: list[str] = []
        for technology_id, technology in sorted(state.technologies.items()):
            if technology.unlocked or not technology.can_unlock(known):
                continue
            project_id = f"research:{technology_id}"
            project = self.projects.setdefault(project_id, ResearchProject(project_id, technology_id))
            project.researchers.update(researchers)
            effort = sum(
                max(0.1, state.agents[agent_id].skills.get("research", state.agents[agent_id].skills.get("science", 0.1)))
                for agent_id in project.researchers
                if agent_id in state.agents
            ) * 0.01 * ticks
            if technology.research(effort, known):
                unlocked_now.append(technology_id)
                self.completed.append(technology_id)
                inventor = min(project.researchers) if project.researchers else researchers[0]
                innovation_id = f"innovation:{technology_id}"
                if innovation_id not in state.innovation.discovered:
                    innovation = Innovation(
                        innovation_id,
                        technology.name,
                        inventor,
                        frozenset(technology.prerequisites),
                        utility=1.0,
                    )
                    state.innovation.discover(innovation, known)
                for agent_id in project.researchers:
                    agent = state.agents.get(agent_id)
                    if agent is not None and agent.health > 0.0:
                        agent.learn(technology_id)
                known.add(technology_id)
        for innovation_id, innovation in sorted(state.innovation.discovered.items()):
            if not innovation_id.startswith("innovation:"):
                continue
            technology_id = innovation_id.removeprefix("innovation:")
            for agent_id in self.researchers_for(technology_id):
                if agent_id in state.agents and state.agents[agent_id].health > 0.0:
                    state.innovation.adopt(innovation_id, agent_id)
        return tuple(unlocked_now)
