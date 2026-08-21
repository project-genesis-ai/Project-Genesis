from __future__ import annotations

from dataclasses import dataclass, field

from genesis.agents.agent import Agent
from genesis.civilization.technology import Technology
from genesis.knowledge.model import Experience, KnowledgeLesson, KnowledgeTransfer
from genesis.knowledge.repository import KnowledgeRepository
from genesis.science.research import ResearchProject


@dataclass(frozen=True, slots=True)
class KnowledgeStepResult:
    transfers: tuple[KnowledgeTransfer, ...] = ()
    domains_taught: tuple[str, ...] = ()


@dataclass(slots=True)
class KnowledgeRuntime:
    """Transfers verified institutional lessons into each living person's learned knowledge."""

    lessons_per_agent_per_step: int = 2
    transfers: list[KnowledgeTransfer] = field(default_factory=list)
    max_transfer_history: int = 100_000

    def __post_init__(self) -> None:
        if self.lessons_per_agent_per_step < 1 or self.max_transfer_history < 1:
            raise ValueError("knowledge runtime limits must be positive")

    def record_experience(self, repository: KnowledgeRepository, experience: Experience) -> None:
        repository.record(experience)

    def publish_research_result(
        self,
        repository: KnowledgeRepository,
        technology: Technology,
        project: ResearchProject,
        tick: int,
    ) -> KnowledgeLesson:
        """Turn a completed research project into evidence-backed institutional knowledge."""
        if tick < 0:
            raise ValueError("knowledge tick cannot be negative")
        if not technology.unlocked:
            raise ValueError("technology must be unlocked before publication")
        if project.technology_id != technology.technology_id:
            raise ValueError("research project does not match technology")
        researchers = tuple(sorted(project.researchers))
        if not researchers:
            raise ValueError("research publication requires at least one researcher")

        evidence_ids: list[str] = []
        for researcher_id in researchers:
            experience_id = f"research:{technology.technology_id}:{researcher_id}"
            existing = repository.domains.get("technology")
            if existing is None or experience_id not in existing.experiences:
                repository.record(
                    Experience(
                        experience_id=experience_id,
                        domain="technology",
                        actor_id=researcher_id,
                        tick=tick,
                        observation=f"completed research for {technology.technology_id}",
                        action=f"research:{technology.technology_id}",
                        outcome=f"unlocked:{technology.technology_id}",
                        success=True,
                        confidence=1.0,
                    )
                )
            evidence_ids.append(experience_id)

        lesson_id = f"technology:{technology.technology_id}"
        existing_lesson = repository.get_lesson("technology", lesson_id)
        if existing_lesson is not None:
            return existing_lesson

        generation = max(
            (lesson.generation for bucket in repository.domains.values() for lesson in bucket.lessons.values()),
            default=-1,
        ) + 1
        return repository.propose_lesson(
            lesson_id=lesson_id,
            domain="technology",
            statement=f"Research established that {technology.name} is achievable under the recorded prerequisites.",
            evidence_ids=tuple(evidence_ids),
            generation=generation,
        )

    def step(self, repository: KnowledgeRepository, agents: dict[str, Agent], tick: int) -> KnowledgeStepResult:
        if tick < 0:
            raise ValueError("knowledge tick cannot be negative")
        transfers: list[KnowledgeTransfer] = []
        taught_domains: set[str] = set()
        for agent_id, agent in sorted(agents.items()):
            if agent.health <= 0.0:
                continue
            lessons = repository.verified_lessons(limit=self.lessons_per_agent_per_step * max(1, len(repository.domains)))
            selected = [lesson for lesson in lessons if lesson.lesson_id not in agent.knowledge][: self.lessons_per_agent_per_step]
            for lesson in selected:
                agent.learn(lesson.lesson_id, lesson.confidence)
                transfer = KnowledgeTransfer(agent_id, lesson.lesson_id, lesson.domain, tick, lesson.confidence)
                transfers.append(transfer)
                taught_domains.add(lesson.domain)
        self.transfers.extend(transfers)
        if len(self.transfers) > self.max_transfer_history:
            del self.transfers[: len(self.transfers) - self.max_transfer_history]
        return KnowledgeStepResult(tuple(transfers), tuple(sorted(taught_domains)))
