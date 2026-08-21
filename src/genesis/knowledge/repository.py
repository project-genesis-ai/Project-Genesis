from __future__ import annotations

from dataclasses import dataclass, field

from genesis.knowledge.model import Experience, KnowledgeLesson, KnowledgeStatus


@dataclass(slots=True)
class DomainKnowledge:
    experiences: dict[str, Experience] = field(default_factory=dict)
    lessons: dict[str, KnowledgeLesson] = field(default_factory=dict)


@dataclass(slots=True)
class KnowledgeRepository:
    """Domain-separated institutional memory with deterministic evidence gates."""

    domains: dict[str, DomainKnowledge] = field(default_factory=dict)
    max_experiences_per_domain: int = 100_000
    max_lessons_per_domain: int = 10_000
    minimum_verification_evidence: int = 3

    def __post_init__(self) -> None:
        if self.max_experiences_per_domain < 1 or self.max_lessons_per_domain < 1:
            raise ValueError("knowledge capacities must be positive")
        if self.minimum_verification_evidence < 2:
            raise ValueError("verification requires at least two independent observations")

    def _domain(self, name: str) -> DomainKnowledge:
        domain = name.strip()
        if not domain:
            raise ValueError("knowledge domain cannot be empty")
        return self.domains.setdefault(domain, DomainKnowledge())

    def record(self, experience: Experience) -> None:
        bucket = self._domain(experience.domain)
        if experience.experience_id in bucket.experiences:
            raise ValueError(f"duplicate experience: {experience.experience_id}")
        bucket.experiences[experience.experience_id] = experience
        while len(bucket.experiences) > self.max_experiences_per_domain:
            oldest = min(bucket.experiences.values(), key=lambda item: (item.tick, item.experience_id))
            del bucket.experiences[oldest.experience_id]

    def propose_lesson(self, *, lesson_id: str, domain: str, statement: str, evidence_ids: tuple[str, ...], generation: int = 0) -> KnowledgeLesson:
        bucket = self._domain(domain)
        if lesson_id in bucket.lessons:
            raise ValueError(f"duplicate lesson: {lesson_id}")
        if len(evidence_ids) != len(set(evidence_ids)) or not evidence_ids:
            raise ValueError("a lesson requires unique evidence")
        experiences = [bucket.experiences.get(item) for item in evidence_ids]
        if any(item is None for item in experiences):
            raise ValueError("all lesson evidence must exist in the same domain")
        assert all(item is not None for item in experiences)
        actors = {item.actor_id for item in experiences}
        confidence = min(1.0, sum(item.confidence for item in experiences) / len(experiences))
        status = KnowledgeStatus.VERIFIED if len(actors) >= 2 and len(evidence_ids) >= self.minimum_verification_evidence else KnowledgeStatus.PROVISIONAL
        lesson = KnowledgeLesson(lesson_id, domain.strip(), statement, tuple(evidence_ids), confidence, status, generation)
        bucket.lessons[lesson_id] = lesson
        while len(bucket.lessons) > self.max_lessons_per_domain:
            oldest = min(bucket.lessons.values(), key=lambda item: (item.generation, item.lesson_id))
            del bucket.lessons[oldest.lesson_id]
        return lesson

    def dispute(self, domain: str, lesson_id: str) -> KnowledgeLesson:
        bucket = self._domain(domain)
        lesson = bucket.lessons.get(lesson_id)
        if lesson is None:
            raise KeyError(lesson_id)
        updated = KnowledgeLesson(lesson.lesson_id, lesson.domain, lesson.statement, lesson.evidence_ids, lesson.confidence, KnowledgeStatus.DISPUTED, lesson.generation)
        bucket.lessons[lesson_id] = updated
        return updated

    def verified_lessons(self, domain: str | None = None, limit: int = 10) -> tuple[KnowledgeLesson, ...]:
        if limit < 0:
            raise ValueError("limit cannot be negative")
        buckets = [self.domains[domain]] if domain is not None and domain in self.domains else ([] if domain is not None else list(self.domains.values()))
        lessons = [lesson for bucket in buckets for lesson in bucket.lessons.values() if lesson.status is KnowledgeStatus.VERIFIED]
        lessons.sort(key=lambda item: (-item.confidence, item.generation, item.domain, item.lesson_id))
        return tuple(lessons[:limit])

    def domains_with_verified_knowledge(self) -> tuple[str, ...]:
        return tuple(sorted(domain for domain in self.domains if self.verified_lessons(domain, 1)))
