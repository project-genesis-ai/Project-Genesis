from genesis.agents.agent import Agent
from genesis.core.simulation import Simulation
from genesis.events.event import SimulationEvent


def test_first_citizen_lifecycle_is_deterministic() -> None:
    simulation = Simulation()
    simulation.add_agent(Agent("citizen-1", "First Citizen"))
    simulation.emit(SimulationEvent(0, "CitizenCreated", actor_id="citizen-1"))

    simulation.step()

    assert simulation.time.tick == 1
    assert simulation.state.agents["citizen-1"].age_ticks == 1
    assert simulation.state.history.at_tick(0)[0].event_type == "CitizenCreated"
