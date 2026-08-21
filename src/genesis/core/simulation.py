from __future__ import annotations

from dataclasses import dataclass, field

from genesis.actions.survival import ConsumeResource
from genesis.agents.agent import Agent
from genesis.cognition.policy import SurvivalPolicy
from genesis.core.clock import SimulationTime
from genesis.core.config import SimulationConfig
from genesis.core.state import SimulationState
from genesis.culture.history import HistoricalEvent
from genesis.events.event import SimulationEvent
from genesis.life.systems import LifeSystem
from genesis.planet.coupling import PlanetEngine
from genesis.planet.terrain import TerrainParams


@dataclass(slots=True)
class Simulation:
    """Deterministic coordinator for the complete physical-to-civilizational simulation."""

    config: SimulationConfig = field(default_factory=SimulationConfig)
    state: SimulationState = field(default_factory=SimulationState)
    time: SimulationTime = field(default_factory=SimulationTime)
    life: LifeSystem = field(default_factory=LifeSystem)
    policy: SurvivalPolicy = field(default_factory=SurvivalPolicy)

    def __post_init__(self) -> None:
        self.state.bind_simulation(self)
        params = self.state.planet.terrain_params
        if params.seed == 0 and self.config.seed != 0 and self.state.planet_snapshot is None:
            self.state.planet = PlanetEngine(TerrainParams(width=params.width, height=params.height, seed=self.config.seed, ocean_fraction=params.ocean_fraction, mountain_strength=params.mountain_strength, island_strength=params.island_strength))
        # The simulation seed is the authoritative seed for stochastic life
        # behavior as well as the planetary generator. Re-seeding only changes
        # the RNG stream; existing species/organism state is preserved.
        self.state.ecosystem.reseed(self.config.seed)

    def add_agent(self, agent: Agent) -> None:
        self.state.add_agent(agent)

    def add_birth(self, child: Agent, parent_ids: tuple[str, ...]) -> None:
        record = self.state.add_birth(child, parent_ids, self.time.tick)
        self.emit(SimulationEvent(self.time.tick, "AgentBorn", actor_id=child.agent_id, data={"parent_ids": record.parent_ids, "birth_id": record.birth_id}))

    def emit(self, event: SimulationEvent) -> None:
        if event.tick != self.time.tick:
            raise ValueError("Event tick must match current simulation time")
        self.state.history.append(event)

    def metrics(self):
        return self.state.metrics()

    def validate(self):
        return self.state.invariants()

    def _advance_needs(self, agent: Agent, ticks: int) -> None:
        agent.needs.decay(hunger=self.config.hunger_per_tick * ticks, thirst=self.config.thirst_per_tick * ticks, energy=self.config.energy_per_tick * ticks, social=self.config.social_per_tick * ticks, comfort=self.config.comfort_per_tick * ticks)

    def _execute_choice(self, agent: Agent) -> None:
        if agent.health <= 0.0:
            return
        cognition = self.state.cognition.observe(agent, self.state.world, self.time.tick)
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
            self.state.cognition.record_action(agent, self.time.tick, "rest", selected.reason)
            self.state.cognition.record_outcome(agent, self.time.tick, f"energy:{min(0.25, before):.6f}", importance=0.3)
            self.emit(SimulationEvent(self.time.tick, "AgentRested", actor_id=agent.agent_id, data={"relief": min(0.25, before), "memory_count": cognition.memory_count}))
            return
        else:
            self.state.cognition.record_action(agent, self.time.tick, "idle", selected.reason)
            self.emit(SimulationEvent(self.time.tick, "AgentIdle", actor_id=agent.agent_id))
            return
        action.execute(agent, self.state.world, self.time)
        self.state.cognition.record_action(agent, self.time.tick, selected.action_name, selected.reason)
        self.state.cognition.record_outcome(agent, self.time.tick, selected.action_name, importance=0.4)
        self.emit(SimulationEvent(self.time.tick, "AgentActionCompleted", actor_id=agent.agent_id, data={"action": selected.action_name, "reason": selected.reason, "memory_count": cognition.memory_count}))

    def _advance_demography_and_labor(self, ticks: int) -> tuple[str, ...]:
        for agent_id, agent in self.state.agents.items():
            self.state.demography.people[agent_id].age_ticks = agent.age_ticks
        deaths = self.state.demography.step(0)
        for agent_id in deaths:
            health = self.state.health.states.get(agent_id)
            if health is not None:
                health.health = 0.0
            for government in self.state.governments.values():
                government.remove_citizen(agent_id)
            self.emit(SimulationEvent(self.time.tick, "AgentDied", actor_id=agent_id, data={"reason": "old_age"}))
        for agent_id, agent in self.state.agents.items():
            person = self.state.demography.people.get(agent_id)
            if person is None or not person.alive or agent.health <= 0.0:
                self.state.labor.fire(agent_id)
                continue
            job_id = self.state.labor.workers.get(agent_id)
            wage = self.state.labor.wage(agent_id, ticks)
            if wage > 0:
                self.state.wallets[agent_id].credit(wage)
                employer_id = self.state.labor.jobs[job_id].employer_id if job_id in self.state.labor.jobs else "labor:issuance"
                self.state.ledger.transfer(f"wage:{self.time.tick}:{agent_id}", self.time.tick, f"employer:{employer_id}", f"wallet:{agent_id}", wage, "labor compensation")
                self.emit(SimulationEvent(self.time.tick, "WagePaid", actor_id=agent_id, data={"amount": wage}))
        self.state.sync_economy_to_agents()
        return deaths

    def _advance_civilization(self, ticks: int) -> None:
        deaths, upgraded = self.state.advance_civilization(ticks)
        for agent_id in deaths:
            for government in self.state.governments.values():
                government.remove_citizen(agent_id)
            self.emit(SimulationEvent(self.time.tick, "AgentDied", actor_id=agent_id, data={"reason": "health"}))
        for settlement_id in upgraded:
            self.emit(SimulationEvent(self.time.tick, "SettlementUpgraded", data={"settlement_id": settlement_id}))

    def _advance_social(self) -> None:
        result = self.state.social_runtime.step(self.state.social, self.state.agents, self.time.tick)
        if result.interactions:
            self.emit(SimulationEvent(self.time.tick, "SocialDynamicsAdvanced", data={"interactions": result.interactions, "trust_changes": result.trust_changes, "friendships": result.friendships, "rivalries": result.rivalries}))

    def _advance_culture(self) -> None:
        result = self.state.culture_runtime.step(self.state.culture, self.state.social, self.state.agents, self.time.tick)
        if result.transmissions:
            self.emit(SimulationEvent(self.time.tick, "CulturalTransmission", data={"transmissions": result.transmissions, "new_knowledge": result.new_knowledge, "traditions": result.traditions}))

    def _advance_knowledge(self) -> None:
        result = self.state.knowledge_runtime.step(self.state.knowledge, self.state.agents, self.time.tick)
        if result.transfers:
            self.emit(SimulationEvent(self.time.tick, "GenerationalKnowledgeTransferred", data={"transfers": len(result.transfers), "domains": result.domains_taught}))

    def _advance_finance(self) -> None:
        published = self.state.publish_verified_trading_knowledge(limit=100)
        if published:
            self.emit(SimulationEvent(self.time.tick, "TradingKnowledgePublished", data={"lessons": published}))
        self.state.sync_economy_to_agents()

    def step(self) -> SimulationTime:
        self.time = self.time.advance(self.config.ticks_per_step)
        ticks = self.config.ticks_per_step
        for agent in self.state.agents.values():
            if agent.health > 0.0:
                agent.advance_age(ticks)
                self._advance_needs(agent, ticks)
        self.state.physics.step(self.config.seconds_per_tick * ticks)
        self.state.health.step(ticks)
        self.state.sync_health_to_agents()
        self._advance_demography_and_labor(ticks)
        self._advance_civilization(ticks)
        self.state.advance_planet(self.time.tick)
        self.state.autonomy.step(self.state, self, ticks)
        self.life.step(self.state.environment, self.state.ecosystem, ticks, simulation_tick=self.time.tick, planet_snapshot=self.state.planet_snapshot)
        for migration in self.life.last_migrations:
            self.emit(SimulationEvent(self.time.tick, "AnimalMigrated", actor_id=migration.organism_id, data={"source": migration.source, "destination": migration.destination, "reason": migration.reason, "urgency": migration.urgency}))
        for agent_id, discoveries in self.state.advance_exploration(self.time.tick).items():
            for discovery in discoveries:
                self.emit(SimulationEvent(self.time.tick, "HumanExplored", actor_id=agent_id, data={"x": discovery.x, "y": discovery.y, "discovery_type": discovery.discovery_type, "value": discovery.value}))
        for disaster in self.state.disasters.step(ticks):
            self.state.culture.record(HistoricalEvent(self.time.tick, "disaster", f"{disaster.kind.value} disaster {disaster.disaster_id} ended"))
            self.emit(SimulationEvent(self.time.tick, "DisasterEnded", data={"disaster_id": disaster.disaster_id, "kind": disaster.kind.value}))
        for government in self.state.governments.values():
            government.tick()
        for agent in self.state.agents.values():
            self._execute_choice(agent)
        self._advance_social()
        self._advance_culture()
        self._advance_knowledge()
        unlocked = self.state.research.step(self.state, ticks)
        for technology_id in unlocked:
            self.emit(SimulationEvent(self.time.tick, "TechnologyUnlocked", data={"technology_id": technology_id}))
        self._advance_finance()
        self.state.sync_health_to_agents()
        self.state.sync_economy_to_agents()
        return self.time
