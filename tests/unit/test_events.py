import pytest

from genesis.events.event import SimulationEvent
from genesis.events.history import EventHistory


def test_history_is_ordered_and_queryable() -> None:
    history = EventHistory()
    history.append(SimulationEvent(0, "WorldCreated"))
    history.append(SimulationEvent(1, "CitizenCreated", actor_id="citizen-1"))
    assert len(history.at_tick(1)) == 1
    assert history.all()[0].event_type == "WorldCreated"


def test_history_rejects_out_of_order_events() -> None:
    history = EventHistory([SimulationEvent(2, "Later")])
    with pytest.raises(ValueError):
        history.append(SimulationEvent(1, "Earlier"))
