from genesis.agents.agent import Agent
from genesis.agents.personality import Personality
from genesis.core.simulation import Simulation
from genesis.cognition.memory import Memory, MemoryStore
from genesis.social import RelationType
from genesis.social.runtime import SocialRuntime


def test_social_runtime_creates_deterministic_interactions_and_groups() -> None:
    simulation = Simulation()
    first = Agent("a", "A", personality=Personality(0.8, 0.5, 0.9, 0.8))
    second = Agent("b", "B", personality=Personality(0.8, 0.5, 0.9, 0.8))
    simulation.add_agent(first)
    simulation.add_agent(second)

    result = SocialRuntime().step(simulation.state.social, simulation.state.agents, 1)

    assert result.interactions == 1
    relation = simulation.state.social.relationships.get("a", "b", RelationType.FRIEND)
    assert relation is not None
    assert relation.interaction_count == 1
    assert relation.trust > 0.5


def test_simulation_tick_makes_social_system_authoritative() -> None:
    simulation = Simulation()
    simulation.add_agent(Agent("a", "A"))
    simulation.add_agent(Agent("b", "B"))

    simulation.step()

    relation = simulation.state.social.relationships.get("a", "b", RelationType.FRIEND)
    assert relation is not None
    assert relation.interaction_count == 1
    assert any(event.event_type == "SocialDynamicsAdvanced" for event in simulation.state.history.all())


def test_memory_store_is_bounded_and_deduplicates_ids() -> None:
    store = MemoryStore(capacity=3)
    for tick in range(5):
        store.remember(Memory(f"m{tick}", "test", f"value-{tick}", tick, importance=tick / 4.0))
    store.remember(Memory("m4", "test", "duplicate-id", 100, importance=1.0))

    assert len(store.memories) == 3
    assert [memory.memory_id for memory in store.recall(limit=3)] == ["m4", "m3", "m2"]
