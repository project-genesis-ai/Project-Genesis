from __future__ import annotations

from dataclasses import dataclass, field

from genesis.agents.agent import Agent
from genesis.knowledge.model import Experience, KnowledgeTransfer
from genesis.knowledge.repository import KnowledgeRepository


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
