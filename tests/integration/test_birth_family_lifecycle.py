from genesis.agents.agent import Agent
from genesis.core.simulation import Simulation
from genesis.social import RelationType


def _adult(agent_id: str, name: str) -> Agent:
    return Agent(agent_id, name, age_ticks=30)


def test_birth_creates_authoritative_agent_demography_and_family_links() -> None:
    simulation = Simulation()
    simulation.add_agent(_adult("p1", "Parent One"))
    simulation.add_agent(_adult("p2", "Parent Two"))

    simulation.add_birth(Agent("c1", "Child"), ("p1", "p2"))

    assert "c1" in simulation.state.agents
    assert simulation.state.demography.people["c1"].age_ticks == 0
    assert simulation.state.demography.births[-1].parent_ids == ("p1", "p2")
    assert simulation.state.social.relationships.get("p1", "c1", RelationType.PARENT) is not None
    assert simulation.state.social.relationships.get("p2", "c1", RelationType.PARENT) is not None
    assert simulation.state.history.all()[-1].event_type == "AgentBorn"


def test_birth_rejects_non_adult_or_missing_parents_atomically() -> None:
    simulation = Simulation()
    simulation.add_agent(_adult("p1", "Parent One"))
    simulation.add_agent(Agent("child", "Too Young", age_ticks=5))

    try:
        simulation.add_birth(Agent("c1", "Child"), ("p1", "child"))
    except ValueError:
        pass
    else:
        raise AssertionError("expected invalid parent rejection")

    assert "c1" not in simulation.state.agents
    assert len(simulation.state.demography.births) == 0
