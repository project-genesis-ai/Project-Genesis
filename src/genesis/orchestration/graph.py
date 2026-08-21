from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from genesis.orchestration.state import SharedState


class EdgeCondition(str, Enum):
    ALWAYS = "always"
    ON_SUCCESS = "success"
    ON_FAILURE = "failure"
    ON_NO_FAILURES = "no_failures"
    ON_APPROVAL = "approval"


@dataclass(frozen=True, slots=True)
class WorkflowNode:
    node_id: str
    agent_id: str
    depends_on: tuple[str, ...] = ()
    condition: EdgeCondition = EdgeCondition.ALWAYS
    checkpoint_id: str | None = None
    max_attempts: int = 1

    def __post_init__(self) -> None:
        if not self.node_id.strip() or not self.agent_id.strip():
            raise ValueError("node_id and agent_id must not be empty")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        if self.checkpoint_id is not None and not self.checkpoint_id.strip():
            raise ValueError("checkpoint_id must not be blank")


@dataclass(slots=True)
class WorkflowGraph:
    nodes: dict[str, WorkflowNode] = field(default_factory=dict)

    def add(self, node: WorkflowNode) -> None:
        if node.node_id in self.nodes:
            raise ValueError(f"duplicate workflow node: {node.node_id}")
        if node.node_id in node.depends_on:
            raise ValueError("node cannot depend on itself")
        self.nodes[node.node_id] = node
        try:
            self.validate()
        except Exception:
            del self.nodes[node.node_id]
            raise

    def validate(self) -> None:
        for node in self.nodes.values():
            missing = [dependency for dependency in node.depends_on if dependency not in self.nodes]
            if missing:
                raise ValueError(f"missing dependencies for {node.node_id}: {missing}")
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node_id: str) -> None:
            if node_id in visiting:
                raise ValueError("workflow graph contains a cycle")
            if node_id in visited:
                return
            visiting.add(node_id)
            for dependency in self.nodes[node_id].depends_on:
                visit(dependency)
            visiting.remove(node_id)
            visited.add(node_id)

        for node_id in sorted(self.nodes):
            visit(node_id)

    def ready(self, completed: set[str], failed: set[str], approvals: set[str]) -> tuple[WorkflowNode, ...]:
        ready: list[WorkflowNode] = []
        for node in sorted(self.nodes.values(), key=lambda item: item.node_id):
            if node.node_id in completed:
                continue
            if not all(dependency in completed or dependency in failed for dependency in node.depends_on):
                continue
            if any(dependency in failed for dependency in node.depends_on) and node.condition not in (EdgeCondition.ON_FAILURE,):
                continue
            if node.condition is EdgeCondition.ON_SUCCESS and any(dependency in failed for dependency in node.depends_on):
                continue
            if node.condition is EdgeCondition.ON_NO_FAILURES and failed:
                continue
            if node.condition is EdgeCondition.ON_APPROVAL:
                checkpoint = node.checkpoint_id or node.node_id
                if checkpoint not in approvals:
                    continue
            ready.append(node)
        return tuple(ready)
