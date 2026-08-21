from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from genesis.orchestration.agents import AgentCapability, AgentDefinition, AgentRegistry, AgentResult, AgentStatus
from genesis.orchestration.graph import EdgeCondition, WorkflowGraph, WorkflowNode
from genesis.orchestration.state import Artifact, Finding, SharedState


@dataclass(frozen=True, slots=True)
class OrchestrationResult:
    status: AgentStatus
    state: SharedState
    executed_nodes: tuple[str, ...]
    blocked_nodes: tuple[str, ...]
    failed_nodes: tuple[str, ...]

    @property
    def verified(self) -> bool:
        return self.status is AgentStatus.SUCCEEDED and not self.state.has_errors()


@dataclass(slots=True)
class Orchestrator:
    """Coordinates specialist agents through deterministic dependency waves."""

    registry: AgentRegistry
    max_agents_per_wave: int = 8
    max_total_nodes: int = 64

    def __post_init__(self) -> None:
        if self.max_agents_per_wave < 1 or self.max_total_nodes < 1:
            raise ValueError("orchestrator limits must be positive")

    def route(self, task: str, limit: int | None = None) -> tuple[AgentDefinition, ...]:
        return self.registry.route(task, limit or self.max_agents_per_wave)

    def build_graph(self, task: str) -> WorkflowGraph:
        specialists = self.route(task)
        graph = WorkflowGraph()
        graph.add(WorkflowNode("research", "researcher"))
        graph.add(WorkflowNode("architecture", "architect", ("research",)))

        previous = ["architecture"]
        for index, agent in enumerate(specialists):
            if agent.agent_id in {"researcher", "architect", "integrator", "reviewer", "human_checkpoint", "ship"}:
                continue
            node_id = f"specialist:{index}:{agent.agent_id}"
            graph.add(WorkflowNode(node_id, agent.agent_id, ("architecture",)))
            previous.append(node_id)

        graph.add(WorkflowNode("integrator", "integrator", tuple(previous), EdgeCondition.ON_SUCCESS))
        graph.add(WorkflowNode("reviewer", "reviewer", ("integrator",), EdgeCondition.ON_SUCCESS))
        graph.add(WorkflowNode("human-checkpoint", "human_checkpoint", ("reviewer",), EdgeCondition.ON_APPROVAL, "high-impact", 1))
        graph.add(WorkflowNode("ship", "ship", ("human-checkpoint",), EdgeCondition.ON_SUCCESS))
        if len(graph.nodes) > self.max_total_nodes:
            raise RuntimeError("workflow exceeds configured node limit")
        return graph

    def execute(self, state: SharedState, graph: WorkflowGraph | None = None) -> OrchestrationResult:
        graph = graph or self.build_graph(state.task)
        graph.validate()
        completed: set[str] = set()
        failed: set[str] = set()
        executed: list[str] = []
        blocked: list[str] = []
        attempts: dict[str, int] = {}

        while len(completed) + len(failed) < len(graph.nodes):
            ready = graph.ready(completed, failed, state.approvals)
            if not ready:
                remaining = set(graph.nodes) - completed - failed
                blocked.extend(sorted(remaining))
                break
            wave = ready[: self.max_agents_per_wave]
            progressed = False
            for node in wave:
                agent = self.registry.get(node.agent_id)
                if node.checkpoint_id and node.condition is EdgeCondition.ON_APPROVAL:
                    if node.checkpoint_id not in state.approvals:
                        blocked.append(node.node_id)
                        continue
                attempts[node.node_id] = attempts.get(node.node_id, 0) + 1
                if attempts[node.node_id] > node.max_attempts:
                    failed.add(node.node_id)
                    state.add_finding(Finding(node.agent_id, f"maximum attempts exceeded for {node.node_id}", "error"))
                    continue
                if not self.registry.acquire(agent.agent_id):
                    blocked.append(node.node_id)
                    continue
                state.active_nodes.add(node.node_id)
                try:
                    result = agent.handler(state, node.node_id)
                except Exception as exc:  # boundary around an untrusted adapter
                    result = AgentResult(AgentStatus.FAILED, f"agent execution error: {exc}", retryable=False)
                finally:
                    state.active_nodes.discard(node.node_id)
                    self.registry.release(agent.agent_id)
                executed.append(node.node_id)
                progressed = True
                if result.summary:
                    severity = "error" if result.status is AgentStatus.FAILED else "info"
                    state.add_finding(Finding(agent.agent_id, result.summary, severity))
                for finding in result.findings:
                    if isinstance(finding, Finding):
                        state.add_finding(finding)
                for artifact in result.artifacts:
                    if isinstance(artifact, Artifact):
                        state.add_artifact(artifact)
                if result.status is AgentStatus.SUCCEEDED:
                    completed.add(node.node_id)
                    state.completed_nodes.append(node.node_id)
                else:
                    failed.add(node.node_id)
                    if result.retryable and attempts[node.node_id] < node.max_attempts:
                        failed.remove(node.node_id)
            if not progressed:
                break

        if failed or state.has_errors():
            status = AgentStatus.FAILED
        elif len(completed) == len(graph.nodes):
            status = AgentStatus.SUCCEEDED
        else:
            status = AgentStatus.BLOCKED
        return OrchestrationResult(status, state, tuple(executed), tuple(sorted(set(blocked))), tuple(sorted(failed)))


def _recording_handler(agent_id: str, role: str):
    def handler(state: SharedState, node_id: str) -> AgentResult:
        state.add_artifact(Artifact(f"{node_id}:result", "agent-result", agent_id, f"{role} completed {node_id}"))
        return AgentResult(AgentStatus.SUCCEEDED, f"{role} completed {node_id}")

    return handler


def default_agent_registry() -> AgentRegistry:
    """Return the standard Genesis specialist fleet.

    These built-in handlers are deterministic coordination agents. Provider-specific
    coding/research implementations can replace a handler at the integration edge
    without changing the graph, state, routing, or verification contracts.
    """

    specs = (
        ("researcher", "Researcher", ("research", "evidence", "reference", "audit")),
        ("architect", "System Architect", ("architecture", "design", "dependency", "schema")),
        ("repository_auditor", "Repository Auditor", ("repository", "audit", "incomplete", "broken")),
        ("planetary", "Planetary Specialist", ("planet", "terrain", "continent", "mountain", "ocean")),
        ("climate", "Climate Specialist", ("climate", "atmosphere", "weather", "storm", "temperature")),
        ("hydrology", "Hydrology Specialist", ("rainfall", "runoff", "river", "lake", "groundwater", "evaporation")),
        ("ocean", "Ocean Specialist", ("ocean", "current", "marine", "deep")),
        ("ecology", "Ecology Specialist", ("ecology", "biome", "vegetation", "food chain", "biomass")),
        ("animal", "Animal Specialist", ("animal", "migration", "population", "behavior")),
        ("evolution", "Evolution Specialist", ("evolution", "genetics", "mutation", "speciation", "lineage")),
        ("human", "Human Systems Specialist", ("human", "physiology", "needs", "cognition", "memory", "personality")),
        ("society", "Society Specialist", ("family", "social", "culture", "tradition", "generation")),
        ("civilization", "Civilization Specialist", ("civilization", "settlement", "building", "agriculture", "education", "labor")),
        ("economy", "Economy Specialist", ("economy", "market", "wage", "trade", "ledger", "finance")),
        ("politics", "Politics Specialist", ("politics", "government", "tax", "law", "election", "institution")),
        ("technology", "Technology Specialist", ("technology", "research", "innovation", "invention")),
        ("transport", "Transport Specialist", ("transport", "road", "route", "logistics")),
        ("knowledge", "Knowledge Specialist", ("knowledge", "learning", "education", "memory", "evidence")),
        ("backend", "Backend Specialist", ("backend", "api", "service", "database")),
        ("security", "Security Specialist", ("security", "auth", "permission", "threat")),
        ("performance", "Performance Specialist", ("performance", "scale", "latency", "memory", "optimization")),
        ("tester", "QA Specialist", ("test", "regression", "invariant", "coverage")),
        ("debugger", "Debugger", ("bug", "failure", "exception", "regression", "debug")),
        ("devops", "DevOps Specialist", ("ci", "cd", "deployment", "workflow", "build")),
        ("integrator", "Integrator", ("integration", "merge", "combine", "conflict")),
        ("reviewer", "Code Reviewer", ("review", "quality", "safety", "correctness")),
        ("human_checkpoint", "Human Checkpoint", ("approval", "high-impact", "irreversible")),
        ("ship", "Ship Gate", ("ship", "release", "verified")),
    )
    agents: list[AgentDefinition] = []
    for agent_id, role, keywords in specs:
        capabilities = (AgentCapability(agent_id, tuple(keywords), 50),)
        agents.append(
            AgentDefinition(
                agent_id=agent_id,
                role=role,
                capabilities=capabilities,
                handler=_recording_handler(agent_id, role),
                requires_human_approval=agent_id == "human_checkpoint",
                risk_level="high" if agent_id in {"security", "ship", "human_checkpoint"} else "low",
            )
        )
    return AgentRegistry(agents)
