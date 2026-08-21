from genesis.agriculture import Crop, Farm
from genesis.agents.agent import Agent
from genesis.core.simulation import Simulation
from genesis.education import Course
from genesis.settlement import Settlement


def test_farm_food_security_is_persistent_and_authoritative() -> None:
    simulation = Simulation()
    agent = Agent("a1", "Ada")
    simulation.add_agent(agent)
    farm = Farm("f1", Crop("wheat", "Wheat", growth_ticks=1, yield_per_area=10.0), area=1.0)
    farm.plant()
    simulation.state.add_farm(farm)

    simulation.step()

    balance = simulation.state.civilization.last_food_balance
    assert balance is not None
    assert balance.production > 0.0
    assert balance.security == 1.0


def test_settlement_population_and_farms_feed_planetary_feedback() -> None:
    simulation = Simulation()
    agent = Agent("a1", "Ada")
    simulation.add_agent(agent)
    settlement = Settlement("s1", "Origin", location=(1, 1))
    simulation.state.add_settlement(settlement)
    simulation.state.assign_agent_to_settlement("a1", "s1")

    simulation.step()

    impact = simulation.state.planet.civilization_impacts[(1, 1)]
    assert impact.population_pressure == 0.001


def test_unassigned_agents_remain_backward_compatible() -> None:
    simulation = Simulation()
    agent = Agent("a1", "Ada")
    simulation.add_agent(agent)

    simulation.step()

    assert simulation.state.agents["a1"] is agent
    assert "a1" not in simulation.state.civilization.agent_settlements


def test_dead_agents_stop_receiving_wages_and_leave_settlement() -> None:
    simulation = Simulation()
    agent = Agent("a1", "Ada", age_ticks=359)
    simulation.add_agent(agent)
    settlement = Settlement("s1", "Origin")
    simulation.state.add_settlement(settlement)
    simulation.state.assign_agent_to_settlement("a1", "s1")

    simulation.step()

    assert agent.health == 0.0
    assert "a1" not in settlement.population
    assert not simulation.state.demography.people["a1"].alive


def test_education_progresses_only_for_alive_students() -> None:
    simulation = Simulation()
    agent = Agent("a1", "Ada")
    simulation.add_agent(agent)
    simulation.state.education.add_course(Course("math", "Mathematics", "math", duration_ticks=2))
    simulation.state.education.enroll("a1", "math")

    simulation.step()

    record = simulation.state.education.students[("a1", "math")]
    assert record.progress == 0.5
    assert not record.completed
