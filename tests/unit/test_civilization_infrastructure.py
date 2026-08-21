from genesis.civilization.government import Government
from genesis.civilization.technology import Technology
from genesis.culture.history import CulturalMemory, HistoricalEvent
from genesis.health import Disease, HealthSystem, Injury
from genesis.infrastructure import Road, TransportMode, TransportNetwork
from genesis.world.disasters import Disaster, DisasterSystem, DisasterType


def test_health_injury_recovery_and_immunity() -> None:
    system = HealthSystem()
    state = system.register("a1")
    state.injure(Injury("cut", 0.4, 2))
    state.infect(Disease("flu", 0.2, duration_ticks=2))
    system.step(2, recovery_rate=0.1)
    assert "cut" not in state.injuries
    assert "flu" not in state.diseases
    assert "flu" in state.immunity
    assert state.health > 0.0


def test_disaster_expires_deterministically() -> None:
    system = DisasterSystem()
    system.start(Disaster("f1", DisasterType.FLOOD, 0.8, 2))
    assert system.step(1) == ()
    ended = system.step(1)
    assert len(ended) == 1
    assert not system.active


def test_transport_shortest_route() -> None:
    network = TransportNetwork()
    network.add(Road("ab", "a", "b", 10, mode=TransportMode.ROAD))
    network.add(Road("bc", "b", "c", 10, mode=TransportMode.ROAD))
    network.add(Road("ac", "a", "c", 30, mode=TransportMode.ROAD))
    assert network.route_time("a", "c") == 20 / 60


def test_government_services_and_technology_progress() -> None:
    government = Government("g", "Civic", population={"a", "b"}, treasury=100)
    government.collect_tax(20)
    assert government.spend("water", 50)
    government.tick()
    assert 0.0 <= government.approval <= 1.0
    tech = Technology("fire", "Controlled Fire", research_cost=10)
    assert not tech.research(5, set())
    assert tech.research(5, set())
    assert tech.unlocked


def test_cultural_memory_preserves_order() -> None:
    memory = CulturalMemory()
    memory.record(HistoricalEvent(1, "birth", "A new citizen was born"))
    memory.record(HistoricalEvent(2, "harvest", "The first harvest succeeded"))
    assert [event.tick for event in memory.recent()] == [1, 2]
