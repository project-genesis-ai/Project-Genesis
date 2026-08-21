from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from genesis.knowledge.model import KnowledgeLesson


class AIProvider(Protocol):
    def answer(self, prompt: str, context: tuple[KnowledgeLesson, ...]) -> str: ...


@dataclass(frozen=True, slots=True)
class LearningMessage:
    learner_id: str
    prompt: str
    response: str
    lesson_ids: tuple[str, ...] = ()


@dataclass(slots=True)
class LearningAssistant:
    """Provider-neutral AI boundary for simulated humans.

    The core simulation never performs network calls. An external model adapter may
    implement AIProvider and receive only authorized institutional context.
    """

    provider: AIProvider | None = None
    authorized_lessons: dict[str, KnowledgeLesson] = field(default_factory=dict)
    history: dict[str, list[LearningMessage]] = field(default_factory=dict)
    max_history_per_learner: int = 500

    def authorize(self, lessons: tuple[KnowledgeLesson, ...]) -> None:
        for lesson in lessons:
            self.authorized_lessons[lesson.lesson_id] = lesson

    def ask(self, learner_id: str, prompt: str, domains: tuple[str, ...] = ()) -> LearningMessage:
        if not learner_id.strip() or not prompt.strip():
            raise ValueError("learner and prompt are required")
        selected = tuple(
            lesson for lesson in sorted(self.authorized_lessons.values(), key=lambda item: item.lesson_id)
            if not domains or lesson.domain in domains
        )
        if self.provider is None:
            response = "No external AI provider is configured; use the institutional lessons to study this topic."
        else:
            response = self.provider.answer(prompt, selected)
        message = LearningMessage(learner_id, prompt, response, tuple(lesson.lesson_id for lesson in selected))
        history = self.history.setdefault(learner_id, [])
        history.append(message)
        if len(history) > self.max_history_per_learner:
            del history[: len(history) - self.max_history_per_learner]
        return message
