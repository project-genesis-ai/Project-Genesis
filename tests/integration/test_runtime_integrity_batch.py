from genesis.agents.agent import Agent
from genesis.core.simulation import Simulation
from genesis.world.disasters import Disaster, DisasterType
from genesis.economy import Job


def test_agent_employer_wage_is_bounded_by_employer_wallet() -> None:
    simulation = Simulation()
    employer = Agent("employer", "Employer", wealth=2.0)
    worker = Agent("worker", "Worker", wealth=0.0)
    simulation.add_agent(employer)
    simulation.add_agent(worker)
    simulation.state.labor.post(Job("job", "Worker", "employer", 5.0))
    assert simulation.state.labor.hire("worker", "job")

    simulation.step()

    assert employer.wealth == 0.0
    assert worker.wealth == 2.0
    assert simulation.validate().ok


def test_active_disaster_changes_agent_state_before_it_ends() -> None:
    simulation = Simulation()
    agent = Agent("a", "A")
    simulation.add_agent(agent)
    simulation.state.disasters.start(Disaster("drought-1", DisasterType.DROUGHT, 1.0, 2))

    initial_thirst = agent.needs.thirst
    initial_health = agent.health
    simulation.step()

    assert agent.needs.thirst > initial_thirst
    assert agent.health < initial_health
    assert any(event.event_type == "DisasterImpactApplied" for event in simulation.state.history.all())
    assert simulation.state.disasters.active


def test_disaster_expiration_is_recorded_after_last_active_tick() -> None:
    simulation = Simulation()
    simulation.add_agent(Agent("a", "A"))
    simulation.state.disasters.start(Disaster("storm-1", DisasterType.STORM, 0.5, 1))

    simulation.step()

    assert not simulation.state.disasters.active
    assert simulation.state.disasters.history[0].disaster_id == "storm-1"
    assert any(event.event_type == "DisasterEnded" for event in simulation.state.history.all())
    assert simulation.validate().ok
