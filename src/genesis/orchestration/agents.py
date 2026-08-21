from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from genesis.orchestration.state import SharedState


class AgentStatus(str, Enum):
    READY = "ready"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class AgentCapability:
    """Domain capability used by the deterministic router."""

    domain: str
    keywords: tuple[str, ...] = ()
    priority: int = 50

    def __post_init__(self) -> None:
        if not self.domain.strip():
            raise ValueError("capability domain must not be empty")
        if self.priority < 0:
            raise ValueError("capability priority must not be negative")

    def score(self, task: str) -> int:
        """Score a task using the declared domain and explicit keywords."""
        normalized = task.casefold()
        score = self.priority
        if self.domain.casefold() in normalized:
            score += 10
        score += sum(10 for keyword in self.keywords if keyword.casefold() in normalized)
        return score


@dataclass(frozen=True, slots=True)
class AgentResult:
    status: AgentStatus
    summary: str
    artifacts: tuple[object, ...] = ()
    findings: tuple[object, ...] = ()
    retryable: bool = False


# Quoted SharedState is required because TYPE_CHECKING imports are erased at runtime.
# A bare SharedState here causes import-time NameError during test collection.
AgentHandler = Callable[["SharedState", str], AgentResult]


@dataclass(frozen=True, slots=True)
class AgentDefinition:
    """Deployable specialist definition.

    A handler may wrap a local deterministic implementation or an external AI/coding
    provider. The orchestration core never assumes that provider and remains
    dependency-free.
    """

    agent_id: str
    role: str
    capabilities: tuple[AgentCapability, ...]
    handler: AgentHandler
    max_concurrency: int = 1
    requires_human_approval: bool = False
    risk_level: str = "low"

    def __post_init__(self) -> None:
        if not self.agent_id.strip() or not self.role.strip():
            raise ValueError("agent_id and role must not be empty")
        if not self.capabilities:
            raise ValueError("agent must expose at least one capability")
        if self.max_concurrency < 1:
            raise ValueError("max_concurrency must be positive")

    def score(self, task: str) -> int:
        return max(capability.score(task) for capability in self.capabilities)


class AgentRegistry:
    """Deterministic registry with duplicate and concurrency safeguards."""

    def __init__(self, agents: Iterable[AgentDefinition] = ()) -> None:
        self._agents: dict[str, AgentDefinition] = {}
        self._running: dict[str, int] = {}
        for agent in agents:
            self.register(agent)

    def register(self, agent: AgentDefinition) -> None:
        if agent.agent_id in self._agents:
            raise ValueError(f"agent already registered: {agent.agent_id}")
        self._agents[agent.agent_id] = agent
        self._running[agent.agent_id] = 0

    def get(self, agent_id: str) -> AgentDefinition:
        try:
            return self._agents[agent_id]
        except KeyError as exc:
            raise KeyError(f"unknown agent: {agent_id}") from exc

    def all(self) -> tuple[AgentDefinition, ...]:
        return tuple(self._agents[key] for key in sorted(self._agents))

    def route(self, task: str, limit: int | None = None) -> tuple[AgentDefinition, ...]:
        if limit is not None and limit < 0:
            raise ValueError("route limit must not be negative")
        ranked = sorted(self._agents.values(), key=lambda agent: (-agent.score(task), agent.agent_id))
        selected = [agent for agent in ranked if agent.score(task) > 50]
        if not selected:
            selected = ranked[:1]
        return tuple(selected if limit is None else selected[:limit])

    def acquire(self, agent_id: str) -> bool:
        agent = self.get(agent_id)
        running = self._running[agent_id]
        if running >= agent.max_concurrency:
            return False
        self._running[agent_id] = running + 1
        return True

    def release(self, agent_id: str) -> None:
        if agent_id not in self._running:
            raise KeyError(f"unknown agent: {agent_id}")
        if self._running[agent_id] <= 0:
            raise RuntimeError(f"agent is not running: {agent_id}")
        self._running[agent_id] -= 1
