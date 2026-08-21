from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class Finding:
    """Evidence-backed observation produced by an agent."""

    source: str
    statement: str
    severity: str = "info"
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Artifact:
    """Structured output passed between workflow nodes."""

    artifact_id: str
    kind: str
    producer: str
    summary: str
    payload: Mapping[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SharedState:
    """Bounded, auditable state shared by cooperating engineering agents.

    The state intentionally contains facts and structured artifacts rather than
    free-form agent transcripts. This prevents context growth and makes routing,
    replay, and conflict detection deterministic.
    """

    task: str
    state_id: str = "workflow"
    requirements: tuple[str, ...] = ()
    facts: list[Finding] = field(default_factory=list)
    decisions: list[Finding] = field(default_factory=list)
    artifacts: list[Artifact] = field(default_factory=list)
    failures: list[Finding] = field(default_factory=list)
    completed_nodes: list[str] = field(default_factory=list)
    active_nodes: set[str] = field(default_factory=set)
    approvals: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)
    max_findings: int = 512
    max_artifacts: int = 512
    max_failures: int = 256

    def __post_init__(self) -> None:
        if not self.task.strip():
            raise ValueError("task must not be empty")
        if self.max_findings < 1 or self.max_artifacts < 1 or self.max_failures < 1:
            raise ValueError("state limits must be positive")

    @property
    def now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def add_finding(self, finding: Finding) -> None:
        target = self.failures if finding.severity == "error" else self.facts
        limit = self.max_failures if finding.severity == "error" else self.max_findings
        target.append(finding)
        if len(target) > limit:
            del target[: len(target) - limit]

    def add_decision(self, decision: Finding) -> None:
        self.decisions.append(decision)
        if len(self.decisions) > self.max_findings:
            del self.decisions[: len(self.decisions) - self.max_findings]

    def add_artifact(self, artifact: Artifact) -> None:
        self.artifacts.append(artifact)
        if len(self.artifacts) > self.max_artifacts:
            del self.artifacts[: len(self.artifacts) - self.max_artifacts]

    def approve(self, checkpoint_id: str) -> None:
        if not checkpoint_id.strip():
            raise ValueError("checkpoint_id must not be empty")
        self.approvals.add(checkpoint_id)

    def has_errors(self) -> bool:
        return bool(self.failures)

    def snapshot(self) -> dict[str, Any]:
        """Return a JSON-friendly audit snapshot without mutable references."""
        return {
            "state_id": self.state_id,
            "task": self.task,
            "requirements": list(self.requirements),
            "facts": [f.statement for f in self.facts],
            "decisions": [d.statement for d in self.decisions],
            "artifacts": [a.artifact_id for a in self.artifacts],
            "failures": [f.statement for f in self.failures],
            "completed_nodes": list(self.completed_nodes),
            "active_nodes": sorted(self.active_nodes),
            "approvals": sorted(self.approvals),
            "metadata": dict(self.metadata),
        }
