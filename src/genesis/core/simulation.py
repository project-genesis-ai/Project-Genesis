from __future__ import annotations

from genesis.agents.agent import Agent
from genesis.cognition.decision import DecisionEngine, DecisionOption, DecisionResult
from genesis.world.world import WorldState
from genesis.actions.survival import ConsumeResource
from genesis.cognition.policy import SurvivalPolicy
from genesis.core.clock import SimulationTime
from genesis.core.config import SimulationConfig
from genesis.core.state import SimulationState
from genesis.culture.history import HistoricalEvent
from genesis.events.event import SimulationEvent
from genesis.life.systems import LifeSystem
from genesis.planet.coupling import PlanetEngine
from genesis.planet.terrain import TerrainParams
from genesis.world.disasters import DisasterType

# Keep the coordinator implementation authoritative; only autonomous choice
# execution is extended here so existing civilization/life systems remain intact.
