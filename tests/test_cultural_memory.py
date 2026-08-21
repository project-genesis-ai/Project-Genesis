import pytest

from genesis.culture.history import CulturalMemory, HistoricalEvent


def test_cultural_memory_evicts_oldest_events_at_capacity() -> None:
    memory = CulturalMemory(capacity=2)
    memory.record(HistoricalEvent(1, "a", "first"))
    memory.record(HistoricalEvent(2, "b", "second"))
    memory.record(HistoricalEvent(3, "c", "third"))

    assert [event.tick for event in memory.recent(10)] == [2, 3]


def test_historical_event_rejects_duplicate_actor_ids() -> None:
    with pytest.raises(ValueError, match="actors must be unique"):
        HistoricalEvent(1, "conflict", "duplicate actors", ("a", "a"))
