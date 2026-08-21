from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SpeechAct(str, Enum):
    GREETING = "greeting"
    INFORM = "inform"
    REQUEST = "request"
    TEACH = "teach"
    NEGOTIATE = "negotiate"
    STORY = "story"


@dataclass(slots=True)
class Lexicon:
    words: dict[str, str] = field(default_factory=dict)
    frequencies: dict[str, int] = field(default_factory=dict)

    def add(self, token: str, meaning: str, count: int = 1) -> None:
        token, meaning = token.strip(), meaning.strip()
        if not token or not meaning or count < 1:
            raise ValueError("token, meaning and positive count are required")
        self.words[token] = meaning
        self.frequencies[token] = self.frequencies.get(token, 0) + count

    def meaning(self, token: str) -> str | None:
        return self.words.get(token)

    def common_words(self, limit: int = 10) -> tuple[str, ...]:
        if limit < 0:
            raise ValueError("limit cannot be negative")
        return tuple(token for token, _ in sorted(self.frequencies.items(), key=lambda item: (-item[1], item[0]))[:limit])


@dataclass(slots=True)
class Language:
    language_id: str
    lexicon: Lexicon = field(default_factory=Lexicon)
    speakers: set[str] = field(default_factory=set)
    generation: int = 0

    def __post_init__(self) -> None:
        if not self.language_id.strip():
            raise ValueError("language_id cannot be empty")
        if self.generation < 0:
            raise ValueError("generation cannot be negative")

    def add_speaker(self, agent_id: str) -> None:
        if not agent_id.strip():
            raise ValueError("agent_id cannot be empty")
        self.speakers.add(agent_id)

    def teach(self, teacher_id: str, learner_id: str, token: str, meaning: str) -> None:
        if teacher_id not in self.speakers:
            raise ValueError("teacher must speak the language")
        self.add_speaker(learner_id)
        self.lexicon.add(token, meaning)

    def speak(self, speaker_id: str, tokens: tuple[str, ...]) -> tuple[str, ...]:
        if speaker_id not in self.speakers:
            raise ValueError("speaker must speak the language")
        return tuple(token for token in tokens if token in self.lexicon.words)
