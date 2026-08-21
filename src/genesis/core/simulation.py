from __future__ import annotations

from dataclasses import dataclass, field

from genesis.agents.agent import Agent
from genesis.core.clock import SimulationTime
from genesis.core.config import SimulationConfig
from genesis.core.state import SimulationState
from genesis.events.event import SimulationEvent


@dataclass(slots=True)
class Simulation:
    """Deterministic simulation coordinator. Domain systems plug into this boundary."""

    config: SimulationConfig = field(default_factory=SimulationConfig)
    state: SimulationState = field(default_factory=SimulationState)
    time: SimulationTime = field(default_factory=SimulationTime)

    def add_agent(self, agent: Agent) -> None:
        self.state.add_agent(agent)

    def emit(self, event: SimulationEvent) -> None:
        if event.tick != self.time.tick:
            raise ValueError("Event tick must match current simulation time")
        self.state.history.append(event)

    def step(self) -> SimulationTime:
        next_time = self.time.advance(self.config.ticks_per_step)
        for agent in self.state.agents.values():
            agent.advance_age(self.config.ticks_per_step)
        self.time = next_time
        return self.time
