from __future__ import annotations

from dataclasses import dataclass, field

from genesis.agents.agent import Agent
from genesis.civilization.government import Government
from genesis.civilization.innovation import InnovationSystem
from genesis.civilization.technology import Technology
from genesis.culture.history import CulturalMemory
from genesis.demography.population import DemographicSystem, HumanLifeState
from genesis.education.education import EducationSystem
from genesis.economy.wallet import Wallet
from genesis.economy.work import LaborMarket
from genesis.events.history import EventHistory
from genesis.health.health import HealthState, HealthSystem
from genesis.infrastructure.transport import TransportNetwork
from genesis.life.ecosystem import Ecosystem
from genesis.physics.world import PhysicsWorld
from genesis.politics.politics import PoliticalSystem
from genesis.world.disasters import DisasterSystem
from genesis.world.environment import Environment
from genesis.world.world import WorldState


@dataclass(slots=True)
class SimulationState:
    """Authoritative mutable state for one deterministic simulation instance."""

    world: WorldState = field(default_factory=WorldState)
    environment: Environment = field(default_factory=Environment)
    physics: PhysicsWorld = field(default_factory=PhysicsWorld)
    ecosystem: Ecosystem = field(default_factory=Ecosystem)
    agents: dict[str, Agent] = field(default_factory=dict)
    history: EventHistory = field(default_factory=EventHistory)
    health: HealthSystem = field(default_factory=HealthSystem)
    disasters: DisasterSystem = field(default_factory=DisasterSystem)
    culture: CulturalMemory = field(default_factory=CulturalMemory)
    transport: TransportNetwork = field(default_factory=TransportNetwork)
    governments: dict[str, Government] = field(default_factory=dict)
    technologies: dict[str, Technology] = field(default_factory=dict)
    demography: DemographicSystem = field(default_factory=DemographicSystem)
    labor: LaborMarket = field(default_factory=LaborMarket)
    wallets: dict[str, Wallet] = field(default_factory=dict)
    education: EducationSystem = field(default_factory=EducationSystem)
    politics: PoliticalSystem = field(default_factory=PoliticalSystem)
    innovation: InnovationSystem = field(default_factory=InnovationSystem)

    def add_agent(self, agent: Agent) -> None:
        if agent.agent_id in self.agents:
            raise ValueError(f"Agent already exists: {agent.agent_id}")
        self.agents[agent.agent_id] = agent
        self.health.register(agent.agent_id, HealthState(health=agent.health))
        self.demography.register(HumanLifeState(agent.agent_id, age_ticks=agent.age_ticks))
        self.wallets[agent.agent_id] = Wallet(agent.agent_id, agent.wealth)

    def sync_health_to_agents(self) -> None:
        for agent_id, agent in self.agents.items():
            state = self.health.states.get(agent_id)
            if state is not None:
                agent.health = state.health

    def sync_economy_to_agents(self) -> None:
        for agent_id, agent in self.agents.items():
            wallet = self.wallets.get(agent_id)
            if wallet is not None:
                agent.wealth = wallet.balance

    def add_government(self, government: Government) -> None:
        if government.government_id in self.governments:
            raise ValueError(f"Government already exists: {government.government_id}")
        self.governments[government.government_id] = government

    def add_technology(self, technology: Technology) -> None:
        if technology.technology_id in self.technologies:
            raise ValueError(f"Technology already exists: {technology.technology_id}")
        self.technologies[technology.technology_id] = technology
