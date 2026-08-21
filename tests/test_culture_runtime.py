from genesis.agents.agent import Agent
from genesis.core.simulation import Simulation
from genesis.social import RelationType, Relationship
from genesis.culture.runtime import CultureRuntime


def test_culture_transmits_knowledge_through_trusted_friendship() -> None:
    simulation = Simulation()
    teacher = Agent("a", "A")
    learner = Agent("b", "B")
    teacher.learn("fire-making")
    simulation.add_agent(teacher)
    simulation.add_agent(learner)
    simulation.state.social.relationships.connect(Relationship("a", "b", RelationType.FRIEND, trust=0.9, affinity=0.8))

    result = CultureRuntime().step(simulation.state.culture, simulation.state.social, simulation.state.agents, 1)

    assert result.transmissions == 1
    assert "fire-making" in learner.knowledge
    assert simulation.state.culture.traditions["shared:fire-making"] == 1
    assert learner.memory.recall("knowledge", 1)[0].content == "fire-making"


def test_simulation_tick_integrates_cultural_transmission() -> None:
    simulation = Simulation()
    first = Agent("a", "A")
    second = Agent("b", "B")
    first.learn("water-storage")
    simulation.add_agent(first)
    simulation.add_agent(second)
    simulation.state.social.relationships.connect(Relationship("a", "b", RelationType.FRIEND, trust=0.9, affinity=0.8))

    simulation.step()

    assert "water-storage" in second.knowledge
    assert any(event.event_type == "CulturalTransmission" for event in simulation.state.history.all())
