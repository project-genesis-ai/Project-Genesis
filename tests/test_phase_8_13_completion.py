from genesis.agents.agent import Agent
from genesis.civilization.government import Government
from genesis.core.config import SimulationConfig
from genesis.core.genesis_runtime import GenesisRuntime
from genesis.core.hardening import audit_state
from genesis.core.scaling import PopulationScaler
from genesis.core.simulation import Simulation
from genesis.orchestration.engineering_loop import EngineeringLoop, EngineeringStage, StageResult


def test_phase8_governance_uses_canonical_state_mappings() -> None:
    simulation = Simulation(config=SimulationConfig(seed=31))
    simulation.add_agent(Agent("a", "A", wealth=100.0))
    government = Government("g", "Government")
    simulation.state.add_government(government)
    simulation.state.governance.register_citizen("g", "a")

    assert simulation.state.governance.bound
    assert simulation.state.governance.wallets is simulation.state.wallets
    assert simulation.state.governance.governments is simulation.state.governments
    before = simulation.state.governance.money_supply()
    collected = simulation.state.governance.collect_taxes("g", {"a": 100.0})
    assert collected > 0.0
    assert simulation.state.governance.reconcile(before)


def test_phase10_engineering_can_resume_and_skip_optional_human_gate() -> None:
    loop = EngineeringLoop(human_gate_required=False)
    for stage in (
        EngineeringStage.RESEARCH,
        EngineeringStage.ARCHITECTURE,
        EngineeringStage.IMPLEMENTATION,
        EngineeringStage.INTEGRATION,
        EngineeringStage.TESTING,
        EngineeringStage.DEBUGGING,
        EngineeringStage.REVIEW,
        EngineeringStage.CI_GATE,
        EngineeringStage.SHIP,
    ):
        loop.record(StageResult(stage, True, (stage.value,)))
    assert loop.ready_to_ship
    assert loop.pending() == ()
    assert loop.evidence[EngineeringStage.CI_GATE] == ("ci_gate",)


def test_phase10_high_impact_work_requires_human_gate() -> None:
    loop = EngineeringLoop(human_gate_required=True)
    for stage in (
        EngineeringStage.RESEARCH,
        EngineeringStage.ARCHITECTURE,
        EngineeringStage.IMPLEMENTATION,
        EngineeringStage.INTEGRATION,
        EngineeringStage.TESTING,
        EngineeringStage.DEBUGGING,
        EngineeringStage.REVIEW,
        EngineeringStage.CI_GATE,
    ):
        loop.record(StageResult(stage, True))
    assert loop.required_stage() is EngineeringStage.HUMAN_GATE
    assert not loop.ready_to_ship
    loop.record(StageResult(EngineeringStage.HUMAN_GATE, True, ("approved",)))
    loop.record(StageResult(EngineeringStage.SHIP, True, ("released",)))
    assert loop.ready_to_ship


def test_phase11_scale_plan_has_stable_lod() -> None:
    scaler = PopulationScaler(region_capacity=10, hybrid_threshold=10, aggregate_threshold=25)
    assert scaler.partition(0) == ()
    assert scaler.partition(9)[0].detail == "individual"
    assert all(item.detail == "hybrid" and item.lod == 1 for item in scaler.partition(20))
    assert all(item.detail == "aggregate" and item.lod == 2 for item in scaler.partition(25))
    assert scaler.partition(25) == scaler.partition(25)


def test_phase12_runtime_verification_is_a_twin_run() -> None:
    runtime = GenesisRuntime(Simulation(config=SimulationConfig(seed=41)))
    runtime.step()
    report = runtime.verify(determinism_steps=1)
    assert report.deterministic
    assert report.invariant_ok
    assert not report.faults


def test_phase13_hardening_reports_nested_economic_faults() -> None:
    simulation = Simulation()
    simulation.add_agent(Agent("a", "A"))
    simulation.state.wallets["a"].balance = -1.0
    report = audit_state(simulation)
    assert not report.ok
    assert not report.non_negative_wallets
    assert "wallet balance below zero" in report.faults
