from genesis.agents.agent import Agent
from genesis.cognition.decision import DecisionEngine, DecisionOption
from genesis.cognition.memory import Memory, MemoryStore
from genesis.society.relationships import RelationshipStore


def test_decision_engine_is_deterministic_on_ties() -> None:
    result = DecisionEngine().choose(Agent("a", "A"), None, [DecisionOption("z", 1.0), DecisionOption("a", 1.0)])
    assert result.selected is not None
    assert result.selected.action_name == "a"


def test_memory_recalls_most_important() -> None:
    store = MemoryStore()
    store.remember(Memory("1", "river", "Water is nearby", 1, importance=0.9))
    store.remember(Memory("2", "river", "It is cold", 2, importance=0.2))
    assert store.recall("river", 1)[0].memory_id == "1"


def test_relationship_store_is_symmetric() -> None:
    store = RelationshipStore()
    assert store.get_or_create("b", "a") is store.get_or_create("a", "b")
