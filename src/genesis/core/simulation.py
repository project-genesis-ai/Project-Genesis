from __future__ import annotations

from dataclasses import dataclass, field

from genesis.actions.survival import ConsumeResource
from genesis.agents.agent import Agent
from genesis.cognition.policy import SurvivalPolicy
from genesis.core.clock import SimulationTime
from genesis.core.config import SimulationConfig
from genesis.core.state import SimulationState
from genesis.events.event import SimulationEvent
from genesis.life.systems import LifeSystem


@dataclass(slots=True)
class Simulation:
    """Deterministic simulation coordinator and authoritative agent runtime."""

    config: SimulationConfig = field(default_factory=SimulationConfig)
    state: SimulationState = field(default_factory=SimulationState)
    time: SimulationTime = field(default_factory=SimulationTime)
    life: LifeSystem = field(default_factory=LifeSystem)
    policy: SurvivalPolicy = field(default_factory=SurvivalPolicy)

    def add_agent(self, agent: Agent) -> None:
        self.state.add_agent(agent)

    def emit(self, event: SimulationEvent) -> None:
        if event.tick != self.time.tick:
            raise ValueError("Event tick must match current simulation time")
        self.state.history.append(event)

    def _advance_needs(self, agent: Agent, ticks: int) -> None:
        agent.needs.decay(
            hunger=self.config.hunger_per_tick * ticks,
            thirst=self.config.thirst_per_tick * ticks,
            energy=self.config.energy_per_tick * ticks,
            social=self.config.social_per_tick * ticks,
            comfort=self.config.comfort_per_tick * ticks,
        )

    def _execute_choice(self, agent: Agent) -> None:
        result = self.policy.choose(agent, self.state.world)
        selected = result.selected
        if selected is None:
            return
        if selected.action_name == "eat":
            action = ConsumeResource("food", "hunger")
        elif selected.action_name == "drink":
            action = ConsumeResource("water", "thirst")
        elif selected.action_name == "rest":
            before = agent.needs.energy
            agent.needs.energy = max(0.0, before - 0.25)
            self.emit(SimulationEvent(self.time.tick, "AgentRested", actor_id=agent.agent_id, data={"relief": min(0.25, before)}))
            return
        else:
            self.emit(SimulationEvent(self.time.tick, "AgentIdle", actor_id=agent.agent_id))
            return
        action.execute(agent, self.state.world, self.time)
        self.emit(
            SimulationEvent(
                self.time.tick,
                "AgentActionCompleted",
                actor_id=agent.agent_id,
                data={"action": selected.action_name, "reason": selected.reason},
            )
        )

    def step(self) -> SimulationTime:
        next_time = self.time.advance(self.config.ticks_per_step)
        self.time = next_time
        for agent in self.state.agents.values():
            agent.advance_age(self.config.ticks_per_step)
            self._advance_needs(agent, self.config.ticks_per_step)
        self.state.physics.step(self.config.seconds_per_tick * self.config.ticks_per_step)
        self.life.step(self.state.environment, self.state.ecosystem, self.config.ticks_per_step)
        for agent in self.state.agents.values():
            self._execute_choice(agent)
        return self.time
