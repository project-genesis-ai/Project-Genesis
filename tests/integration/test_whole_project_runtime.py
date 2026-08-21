from genesis.agents.agent import Agent
from genesis.civilization.government import Government
from genesis.civilization.technology import Technology
from genesis.core.simulation import Simulation
from genesis.core.state import SimulationState
from genesis.economy.ledger import DoubleEntryLedger, LedgerEntry, LedgerTransaction
from genesis.economy.work import Job
from genesis.planet.coupling import PlanetEngine
from genesis.planet.terrain import TerrainParams


def small_simulation() -> Simulation:
    state = SimulationState(planet=PlanetEngine(TerrainParams(width=8, height=8, seed=7)))
    return Simulation(state=state)


def test_double_entry_ledger_rejects_unbalanced_transactions() -> None:
    ledger = DoubleEntryLedger()
    transaction = LedgerTransaction(
        "t1",
        1,
        (
            LedgerEntry("t1", 1, "a", -10.0),
            LedgerEntry("t1", 1, "b", 9.0),
        ),
    )
    try:
        ledger.post(transaction)
    except ValueError as exc:
        assert "balanced" in str(exc)
    else:
        raise AssertionError("unbalanced transaction was accepted")


def test_simulation_wires_movement_education_labor_tax_and_ledger() -> None:
    simulation = small_simulation()
    agent = Agent("human-1", "Ada", wealth=100.0, skills={"exploration_range": 1.0})
    simulation.add_agent(agent)
    simulation.state.civilization.add_settlement(__import__("genesis.settlement.settlements", fromlist=["Settlement"]).Settlement("s1", "Home", location=(3, 3)))
    simulation.state.civilization.assign_agent("human-1", "s1")
    simulation.state.labor.post(Job("job-1", "Researcher", "lab", 2.0, "research"))
    government = Government("gov-1", "Genesis", population={"human-1"}, laws={"income_tax": 0.10})
    simulation.state.add_government(government)

    simulation.step()

    assert simulation.state.education.students
    assert "human-1" in simulation.state.labor.workers
    assert simulation.state.ledger.transactions
    assert simulation.state.ledger.balance("wallet:human-1") < 0.0 or agent.wealth > 100.0
    assert any(event.event_type == "HumanMoved" for event in simulation.state.history.all())


def test_research_unlocks_technology_and_creates_innovation() -> None:
    simulation = small_simulation()
    simulation.add_agent(Agent("scientist", "Scientist", skills={"research": 1.0}))
    simulation.state.add_technology(Technology("fire", "Controlled Fire", research_cost=0.001))

    simulation.step()

    assert simulation.state.technologies["fire"].unlocked
    assert "innovation:fire" in simulation.state.innovation.discovered
    assert any(event.event_type == "TechnologyUnlocked" for event in simulation.state.history.all())


def test_metrics_and_invariants_are_available_after_ticks() -> None:
    simulation = small_simulation()
    simulation.add_agent(Agent("human-1", "Explorer"))
    simulation.step()

    metrics = simulation.metrics()
    report = simulation.validate()

    assert metrics.tick == 1
    assert metrics.population == 1
    assert metrics.event_count == len(simulation.state.history.all())
    assert report.ok, report.violations
