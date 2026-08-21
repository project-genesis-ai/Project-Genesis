from __future__ import annotations

from dataclasses import dataclass, field

from genesis.agents.agent import Agent
from genesis.civilization.autonomy import CivilizationAutonomy
from genesis.civilization.government import Government
from genesis.civilization.governance_runtime import GovernanceRuntime
from genesis.civilization.innovation import InnovationSystem
from genesis.civilization.runtime import CivilizationRuntime
from genesis.civilization.technology import Technology
from genesis.core.metrics import InvariantReport, SimulationMetrics, collect_metrics, validate_invariants
from genesis.culture.history import CulturalMemory
from genesis.culture.runtime import CultureRuntime
from genesis.demography.population import AgeStage, BirthRecord, DemographicSystem, HumanLifeState
from genesis.education.ai_assistant import LearningAssistant
from genesis.education.education import EducationSystem
from genesis.economy.accounting import DoubleEntryLedger
from genesis.economy.wallet import Wallet
from genesis.economy.work import LaborMarket
from genesis.events.history import EventHistory
from genesis.finance.trading import TradingCompany, TradingLesson
from genesis.health.health import HealthState, HealthSystem
from genesis.infrastructure.transport import TransportNetwork
from genesis.infrastructure.utilities import UtilityNetwork
from genesis.life.ecosystem import Ecosystem
from genesis.physics.world import PhysicsWorld
from genesis.politics.politics import PoliticalSystem
from genesis.resources.stock import ResourceStock
from genesis.science.research import ResearchSystem
from genesis.social.runtime import SocialRuntime
from genesis.social.social import SocialSystem
from genesis.world.disasters import DisasterSystem
from genesis.world.environment import Environment
from genesis.world.world import WorldState
from genesis.planet.coupling import PlanetEngine, PlanetSnapshot
from genesis.planet.exploration import Discovery
from genesis.planet.exploration_runtime import ExplorerState, ExplorationRuntime
from genesis.planet.runtime import PlanetEcologyRuntime
from genesis.cognition.runtime import CognitionRuntime
from genesis.knowledge.repository import KnowledgeRepository
from genesis.knowledge.runtime import KnowledgeRuntime


@dataclass(slots=True)
class SimulationState:
    """Authoritative mutable state for one deterministic simulation instance."""

    world: WorldState = field(default_factory=WorldState)
    environment: Environment = field(default_factory=Environment)
    physics: PhysicsWorld = field(default_factory=PhysicsWorld)
    ecosystem: Ecosystem = field(default_factory=Ecosystem)
    resources: ResourceStock = field(default_factory=ResourceStock)
    utilities: UtilityNetwork = field(default_factory=UtilityNetwork)
    agents: dict[str, Agent] = field(default_factory=dict)
    history: EventHistory = field(default_factory=EventHistory)
    health: HealthSystem = field(default_factory=HealthSystem)
    disasters: DisasterSystem = field(default_factory=DisasterSystem)
    culture: CulturalMemory = field(default_factory=CulturalMemory)
    culture_runtime: CultureRuntime = field(default_factory=CultureRuntime)
    transport: TransportNetwork = field(default_factory=TransportNetwork)
    governments: dict[str, Government] = field(default_factory=dict)
    governance: GovernanceRuntime = field(default_factory=GovernanceRuntime)
    technologies: dict[str, Technology] = field(default_factory=dict)
    demography: DemographicSystem = field(default_factory=DemographicSystem)
    labor: LaborMarket = field(default_factory=LaborMarket)
    wallets: dict[str, Wallet] = field(default_factory=dict)
    ledger: DoubleEntryLedger = field(default_factory=DoubleEntryLedger)
    education: EducationSystem = field(default_factory=EducationSystem)
    learning_assistant: LearningAssistant = field(default_factory=LearningAssistant)
    politics: PoliticalSystem = field(default_factory=PoliticalSystem)
    innovation: InnovationSystem = field(default_factory=InnovationSystem)
    research: ResearchSystem = field(default_factory=ResearchSystem)
    social: SocialSystem = field(default_factory=SocialSystem)
    social_runtime: SocialRuntime = field(default_factory=SocialRuntime)
    cognition: CognitionRuntime = field(default_factory=CognitionRuntime)
    knowledge: KnowledgeRepository = field(default_factory=KnowledgeRepository)
    knowledge_runtime: KnowledgeRuntime = field(default_factory=KnowledgeRuntime)
    planet: PlanetEngine = field(default_factory=PlanetEngine)
    planet_ecology: PlanetEcologyRuntime = field(default_factory=PlanetEcologyRuntime)
    exploration: ExplorationRuntime = field(default_factory=ExplorationRuntime)
    exploration_discoveries: dict[str, tuple[Discovery, ...]] = field(default_factory=dict)
    planet_snapshot: PlanetSnapshot | None = None
    civilization: CivilizationRuntime = field(default_factory=CivilizationRuntime)
    autonomy: CivilizationAutonomy = field(default_factory=CivilizationAutonomy)
    trading_company: TradingCompany = field(default_factory=lambda: TradingCompany("genesis-trading"))
    _simulation_ref: object | None = field(default=None, init=False, repr=False)

    def add_agent(self, agent: Agent) -> None:
        if agent.agent_id in self.agents:
            raise ValueError(f"Agent already exists: {agent.agent_id}")
        self.agents[agent.agent_id] = agent
        self.health.register(agent.agent_id, HealthState(health=agent.health))
        self.demography.register(HumanLifeState(agent.agent_id, age_ticks=agent.age_ticks))
        self.wallets[agent.agent_id] = Wallet(agent.agent_id, agent.wealth)

    def add_birth(self, child: Agent, parent_ids: tuple[str, ...], tick: int) -> BirthRecord:
        if tick < 0 or len(parent_ids) != 2 or len(set(parent_ids)) != 2:
            raise ValueError("a birth requires exactly two distinct parents and a non-negative tick")
        if any(parent_id not in self.agents for parent_id in parent_ids):
            raise ValueError("all birth parents must exist")
        for parent_id in parent_ids:
            parent = self.demography.people[parent_id]
            if not parent.alive or parent.stage is not AgeStage.ADULT or parent.fertility <= 0.0:
                raise ValueError("birth parents must be living fertile adults")
        if child.agent_id in self.agents:
            raise ValueError(f"Agent already exists: {child.agent_id}")
        record = BirthRecord(f"birth:{tick}:{child.agent_id}", parent_ids, child.agent_id, tick)
        self.add_agent(child)
        self.demography.births.append(record)
        for parent_id in parent_ids:
            self.social.establish_family(parent_id, child.agent_id)
        parent_settlements = [self.civilization.agent_settlements.get(parent_id) for parent_id in parent_ids]
        target = parent_settlements[0] if parent_settlements[0] == parent_settlements[1] else next((value for value in parent_settlements if value is not None), None)
        if target is not None:
            self.civilization.assign_agent(child.agent_id, target)
        return record

    def record_knowledge_experience(self, experience) -> None:
        self.knowledge_runtime.record_experience(self.knowledge, experience)

    def publish_verified_trading_knowledge(self, limit: int = 100) -> tuple[str, ...]:
        lessons = self.knowledge.verified_lessons("trading", limit)
        published: list[str] = []
        for lesson in lessons:
            self.trading_company.academy.publish(TradingLesson(lesson.lesson_id, lesson.domain, lesson.statement, len(lesson.evidence_ids), lesson.confidence))
            self.learning_assistant.authorize((lesson,))
            published.append(lesson.lesson_id)
        return tuple(published)

    def add_farm(self, farm) -> None:
        self.civilization.add_farm(farm)

    def add_settlement(self, settlement) -> None:
        self.civilization.add_settlement(settlement)

    def assign_agent_to_settlement(self, agent_id: str, settlement_id: str) -> None:
        if agent_id not in self.agents:
            raise ValueError(f"unknown agent: {agent_id}")
        self.civilization.assign_agent(agent_id, settlement_id)

    def register_trader(self, agent_id: str, capital_limit: float = 0.0) -> None:
        if agent_id not in self.agents:
            raise ValueError(f"unknown agent: {agent_id}")
        self.trading_company.exchange.register_trader(agent_id, self.wallets[agent_id])
        from genesis.finance.trading import TraderProfile
        self.trading_company.hire(TraderProfile(agent_id), capital_limit)

    def _apply_planet_ecology(self, snapshot: PlanetSnapshot) -> None:
        self.planet_ecology.apply_to_ecosystem(self.ecosystem, snapshot)
        aggregates: dict[str, tuple[float, float, int]] = {}
        for row in snapshot.cells:
            for cell in row:
                biome_name = cell.biome.name
                productivity = max(0.0, min(1.0, cell.biome.vegetation_productivity))
                moisture = max(0.0, min(1.0, cell.hydrology.groundwater_mm / 50.0))
                previous = aggregates.get(biome_name, (0.0, 0.0, 0))
                aggregates[biome_name] = (previous[0] + productivity, previous[1] + moisture, previous[2] + 1)
        for biome_name, (productivity_sum, moisture_sum, count) in sorted(aggregates.items()):
            self.planet_ecology.step_terrestrial_biomass(biome_name, productivity=productivity_sum / count, moisture=moisture_sum / count)

    def initialize_planet(self) -> None:
        if self.planet_snapshot is None:
            self.planet_snapshot = self.planet.step(0)
            self.environment.sync_from_planet(self.planet_snapshot)
            self._apply_planet_ecology(self.planet_snapshot)

    def advance_planet(self, tick: int) -> None:
        snapshot = self.planet.step(tick)
        self.environment.sync_from_planet(snapshot)
        self._apply_planet_ecology(snapshot)
        self.planet_snapshot = snapshot

    def advance_exploration(self, tick: int) -> dict[str, tuple[Discovery, ...]]:
        if tick < 0:
            raise ValueError("tick cannot be negative")
        if self.planet_snapshot is None:
            raise RuntimeError("planet must be advanced before exploration")
        terrain = tuple(tuple(cell_state.terrain for cell_state in row) for row in self.planet_snapshot.cells)
        discoveries_by_agent: dict[str, tuple[Discovery, ...]] = {}
        for agent in self.agents.values():
            if agent.health <= 0.0:
                continue
            configured_range = agent.skills.get("exploration_range", 1.0)
            movement_range = max(0, min(16, int(round(configured_range))))
            explorer = ExplorerState(agent.agent_id, agent.world_x, agent.world_y, movement_range)
            discoveries = self.exploration.explore(explorer, terrain, tick)
            for discovery in discoveries:
                agent.learn(f"terrain:{discovery.x}:{discovery.y}:{discovery.discovery_type}")
            discoveries_by_agent[agent.agent_id] = discoveries
        self.exploration_discoveries = discoveries_by_agent
        return discoveries_by_agent

    def advance_civilization(self, ticks: int) -> tuple[tuple[str, ...], tuple[str, ...]]:
        return self.civilization.step(self, ticks)

    def add_government(self, government: Government) -> None:
        if government.government_id in self.governments:
            raise ValueError(f"Government already exists: {government.government_id}")
        self.governments[government.government_id] = government

    def add_technology(self, technology: Technology) -> None:
        if technology.technology_id in self.technologies:
            raise ValueError(f"Technology already exists: {technology.technology_id}")
        self.technologies[technology.technology_id] = technology

    def metrics(self) -> SimulationMetrics:
        if self._simulation_ref is None:
            raise RuntimeError("simulation state is not bound to a Simulation")
        return collect_metrics(self._simulation_ref)

    def invariants(self) -> InvariantReport:
        if self._simulation_ref is None:
            raise RuntimeError("simulation state is not bound to a Simulation")
        return validate_invariants(self._simulation_ref)

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

    def bind_simulation(self, simulation: object) -> None:
        self._simulation_ref = simulation
        self.governance.bind(self.governments, self.wallets)
