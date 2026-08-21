from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from genesis.core.simulation import Simulation


@dataclass(frozen=True, slots=True)
class SimulationMetrics:
    tick: int
    population: int
    living_population: int
    settlements: int
    cities: int
    farms: int
    employed: int
    educated: int
    technologies_unlocked: int
    innovations: int
    known_regions: int
    discovered_species: int
    average_health: float
    total_wealth: float
    event_count: int


@dataclass(frozen=True, slots=True)
class InvariantReport:
    ok: bool
    violations: tuple[str, ...]


def collect_metrics(simulation: Simulation) -> SimulationMetrics:
    state = simulation.state
    living = [
        agent_id for agent_id, agent in state.agents.items()
        if agent.health > 0.0 and state.demography.people.get(agent_id) is not None and state.demography.people[agent_id].alive
    ]
    health_values = [state.agents[agent_id].health for agent_id in living]
    cities = sum(1 for settlement in state.civilization.settlements.values() if settlement.kind.value == "city")
    educated = sum(1 for record in state.education.students.values() if record.completed)
    known_regions = sum(len(knowledge.explored) for knowledge in state.exploration.terrain_engine.knowledge.values())
    species = sum(len(registry.known_species) for registry in [state.exploration.species_registry]) if hasattr(state.exploration.species_registry, "known_species") else 0
    return SimulationMetrics(
        tick=simulation.time.tick,
        population=len(state.agents),
        living_population=len(living),
        settlements=len(state.civilization.settlements),
        cities=cities,
        farms=len(state.civilization.farms),
        employed=len(state.labor.workers),
        educated=educated,
        technologies_unlocked=sum(1 for technology in state.technologies.values() if technology.unlocked),
        innovations=len(state.innovation.discovered),
        known_regions=known_regions,
        discovered_species=species,
        average_health=sum(health_values) / len(health_values) if health_values else 0.0,
        total_wealth=sum(wallet.balance for wallet in state.wallets.values()),
        event_count=len(state.history.all()),
    )


def validate_invariants(simulation: Simulation) -> InvariantReport:
    state = simulation.state
    violations: list[str] = []
    if any(agent.health < 0.0 or agent.health > 1.0 for agent in state.agents.values()):
        violations.append("agent health outside [0,1]")
    if any(wallet.balance < 0.0 for wallet in state.wallets.values()):
        violations.append("negative wallet balance")
    if set(state.agents) != set(state.wallets):
        violations.append("agent/wallet identity mismatch")
    if any(agent_id not in state.demography.people for agent_id in state.agents):
        violations.append("agent/demography identity mismatch")
    if any(agent_id not in state.health.states for agent_id in state.agents):
        violations.append("agent/health identity mismatch")
    for settlement_id, settlement in state.civilization.settlements.items():
        if any(agent_id not in state.agents for agent_id in settlement.population):
            violations.append(f"settlement {settlement_id} contains unknown resident")
    for government_id, government in state.governments.items():
        if any(agent_id not in state.agents for agent_id in government.population):
            violations.append(f"government {government_id} contains unknown citizen")
    return InvariantReport(not violations, tuple(violations))
