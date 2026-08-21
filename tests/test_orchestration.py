from __future__ import annotations

from genesis.orchestration import (
    AgentCapability,
    AgentDefinition,
    AgentRegistry,
    AgentResult,
    AgentStatus,
    Finding,
    Orchestrator,
    SharedState,
    WorkflowGraph,
    WorkflowNode,
)
from genesis.orchestration.orchestrator import default_agent_registry


def _ok_handler(state: SharedState, node_id: str) -> AgentResult:
    state.add_finding(Finding("test-agent", f"completed {node_id}"))
    return AgentResult(AgentStatus.SUCCEEDED, "ok")


def test_registry_routes_domain_specialists_deterministically() -> None:
    registry = default_agent_registry()
    first = [agent.agent_id for agent in registry.route("improve planetary hydrology and groundwater")]
    second = [agent.agent_id for agent in registry.route("improve planetary hydrology and groundwater")]
    assert first == second
    assert "hydrology" in first
    assert "planetary" in first


def test_capability_domain_is_part_of_routing_score() -> None:
    capability = AgentCapability("hydrology", ("rainfall",), 50)
    assert capability.score("improve hydrology") == 60
    assert capability.score("improve rainfall") == 60


def test_registry_honors_zero_and_bounded_route_limits() -> None:
    registry = default_agent_registry()
    assert registry.route("improve hydrology", limit=0) == ()
    assert len(registry.route("improve hydrology", limit=1)) == 1


def test_graph_rejects_cycles_and_missing_dependencies() -> None:
    graph = WorkflowGraph()
    graph.add(WorkflowNode("a", "a"))
    try:
        graph.add(WorkflowNode("b", "b", ("missing",)))
    except ValueError as exc:
        assert "missing dependencies" in str(exc)
    else:
        raise AssertionError("missing dependency should be rejected")

    cyclic = WorkflowGraph()
    cyclic.nodes["a"] = WorkflowNode("a", "a", ("b",))
    cyclic.nodes["b"] = WorkflowNode("b", "b", ("a",))
    try:
        cyclic.validate()
    except ValueError as exc:
        assert "cycle" in str(exc)
    else:
        raise AssertionError("cycle should be rejected")


def test_normal_task_ships_without_human_checkpoint() -> None:
    registry = default_agent_registry()
    orchestrator = Orchestrator(registry, max_agents_per_wave=6)
    state = SharedState("add a deterministic regression test for ecology")
    result = orchestrator.execute(state)
    assert result.verified
    assert "human-checkpoint" not in result.executed_nodes
    assert "ship" in result.executed_nodes


def test_high_impact_task_blocks_until_human_approval() -> None:
    registry = default_agent_registry()
    orchestrator = Orchestrator(registry, max_agents_per_wave=6)
    state = SharedState("deploy irreversible production database migration")
    blocked = orchestrator.execute(state)
    assert blocked.status is AgentStatus.BLOCKED
    assert "human-checkpoint" in blocked.blocked_nodes
    assert "ship" in blocked.blocked_nodes

    state.approve("high-impact")
    approved = orchestrator.execute(state)
    assert approved.verified
    assert "human-checkpoint" in approved.executed_nodes
    assert "ship" in approved.executed_nodes


def test_custom_agent_handler_failure_isolated_and_reported() -> None:
    def failing_handler(state: SharedState, node_id: str) -> AgentResult:
        raise RuntimeError("adapter failure")

    registry = AgentRegistry(
        [AgentDefinition("researcher", "research", (AgentCapability("research", ("test",), 50),), _ok_handler),
         AgentDefinition("architect", "architect", (AgentCapability("architecture", ("test",), 50),), _ok_handler),
         AgentDefinition("integrator", "integrator", (AgentCapability("integration", ("test",), 50),), _ok_handler),
         AgentDefinition("reviewer", "reviewer", (AgentCapability("review", ("test",), 50),), _ok_handler),
         AgentDefinition("ship", "ship", (AgentCapability("ship", ("test",), 50),), _ok_handler),
         AgentDefinition("broken", "broken", (AgentCapability("broken", ("test",), 100),), failing_handler)],
    )
    orchestrator = Orchestrator(registry, max_agents_per_wave=8)
    result = orchestrator.execute(SharedState("test broken adapter"))
    assert result.status is AgentStatus.FAILED
    assert result.failed_nodes
    assert result.state.has_errors()
