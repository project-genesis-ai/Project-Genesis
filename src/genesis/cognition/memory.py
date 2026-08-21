from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Memory:
    memory_id: str
    subject: str
    content: str
    created_tick: int
    importance: float = 0.5
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not self.memory_id.strip() or not self.subject.strip() or not self.content.strip():
            raise ValueError("memory identity and content cannot be empty")
        if self.created_tick < 0:
            raise ValueError("created_tick cannot be negative")
        if not 0.0 <= self.importance <= 1.0 or not 0.0 <= self.confidence <= 1.0:
            raise ValueError("importance and confidence must be between 0 and 1")


@dataclass(slots=True)
class MemoryStore:
    memories: list[Memory] = field(default_factory=list)

    def remember(self, memory: Memory) -> None:
        self.memories.append(memory)

    def recall(self, subject: str | None = None, limit: int = 10) -> list[Memory]:
        if limit < 1:
            return []
        candidates = self.memories if subject is None else [m for m in self.memories if m.subject == subject]
        return sorted(candidates, key=lambda m: (m.importance * m.confidence, m.created_tick), reverse=True)[:limit]
