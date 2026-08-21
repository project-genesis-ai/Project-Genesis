from __future__ import annotations

from dataclasses import dataclass
import math
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
    agent_ids = set(state.agents)

    if any(not math.isfinite(agent.health) or agent.health < 0.0 or agent.health > 1.0 for agent in state.agents.values()):
        violations.append("agent health outside [0,1]")
    if any(not math.isfinite(agent.wealth) or agent.wealth < 0.0 for agent in state.agents.values()):
        violations.append("agent wealth invalid")
    if any(not math.isfinite(wallet.balance) or wallet.balance < 0.0 for wallet in state.wallets.values()):
        violations.append("negative or non-finite wallet balance")

    if set(state.wallets) != agent_ids:
        violations.append("agent/wallet identity mismatch")
    if set(state.demography.people) != agent_ids:
        violations.append("agent/demography identity mismatch")
    if set(state.health.states) != agent_ids:
        violations.append("agent/health identity mismatch")
    for agent_id, agent in state.agents.items():
        wallet = state.wallets.get(agent_id)
        if wallet is not None and abs(wallet.balance - agent.wealth) > 1e-9:
            violations.append(f"agent/wallet balance mismatch: {agent_id}")

    for settlement_id, settlement in state.civilization.settlements.items():
        for agent_id in settlement.population:
            if agent_id not in agent_ids:
                violations.append(f"settlement {settlement_id} contains unknown resident")
                continue
            if state.civilization.agent_settlements.get(agent_id) != settlement_id:
                violations.append(f"settlement mapping mismatch: {agent_id}")
    for agent_id, settlement_id in state.civilization.agent_settlements.items():
        if agent_id not in agent_ids:
            violations.append(f"settlement mapping contains unknown agent: {agent_id}")
        elif settlement_id not in state.civilization.settlements:
            violations.append(f"settlement mapping contains unknown settlement: {settlement_id}")
        elif agent_id not in state.civilization.settlements[settlement_id].population:
            violations.append(f"settlement mapping mismatch: {agent_id}")

    for agent_id, job_id in state.labor.workers.items():
        if agent_id not in agent_ids:
            violations.append(f"labor worker contains unknown agent: {agent_id}")
        if job_id not in state.labor.jobs:
            violations.append(f"labor worker contains unknown job: {job_id}")
        person = state.demography.people.get(agent_id)
        if person is not None and not person.alive:
            violations.append(f"dead agent remains employed: {agent_id}")

    for government_id, government in state.governments.items():
        if not math.isfinite(government.treasury) or government.treasury < 0.0:
            violations.append(f"government {government_id} treasury invalid")
        if any(agent_id not in agent_ids for agent_id in government.population):
            violations.append(f"government {government_id} contains unknown citizen")

    for faction_id, faction in state.politics.factions.items():
        if any(agent_id not in agent_ids for agent_id in faction.members):
            violations.append(f"political faction {faction_id} contains unknown member")
        if not math.isfinite(faction.influence) or not 0.0 <= faction.influence <= 1.0:
            violations.append(f"political faction {faction_id} influence invalid")
    for election_id, election in state.politics.elections.items():
        if len(set(election.candidates)) != len(election.candidates):
            violations.append(f"election {election_id} has duplicate candidates")
        if any(candidate not in election.candidates or votes < 0 for candidate, votes in election.votes.items()):
            violations.append(f"election {election_id} has invalid votes")
    for treaty_id, treaty in state.politics.treaties.items():
        if len(treaty.parties) < 2 or len(set(treaty.parties)) != len(treaty.parties) or not treaty.active:
            violations.append(f"treaty {treaty_id} is invalid or expired")
    for pair, intensity in state.politics.conflicts.items():
        if len(pair) != 2 or pair[0] == pair[1] or not math.isfinite(intensity) or not 0.0 <= intensity <= 1.0:
            violations.append("political conflict state invalid")

    for (agent_id, _course_id), record in state.education.students.items():
        if agent_id not in agent_ids:
            violations.append(f"education contains unknown student: {agent_id}")
        if record.completed and record.progress < 1.0 - 1e-9:
            violations.append(f"completed education record has incomplete progress: {agent_id}")

    if not state.ledger.is_balanced():
        violations.append("double-entry ledger is unbalanced")
    if any(transaction.tick > simulation.time.tick for transaction in state.ledger.transactions):
        violations.append("ledger transaction is from a future tick")

    events = state.history.all()
    if any(event.tick > simulation.time.tick for event in events):
        violations.append("event history contains a future event")
    if any(left.tick > right.tick for left, right in zip(events, events[1:])):
        violations.append("event history is not monotonic")

    if state.planet_snapshot is not None:
        snapshot = state.planet_snapshot
        if snapshot.tick != simulation.time.tick:
            violations.append("planet snapshot tick mismatch")
        if snapshot.cells:
            width = len(snapshot.cells[0])
            if width == 0 or any(len(row) != width for row in snapshot.cells):
                violations.append("planet snapshot grid is not rectangular")
            for row in snapshot.cells:
                for cell in row:
                    nonnegative_values = (
                        cell.terrain.slope,
                        cell.atmosphere.pressure_kpa,
                        cell.atmosphere.humidity,
                        cell.hydrology.rainfall_mm,
                        cell.hydrology.runoff_mm,
                        cell.hydrology.infiltration_mm,
                        cell.hydrology.groundwater_mm,
                        cell.hydrology.river_flow,
                        cell.hydrology.lake_storage,
                        cell.hydrology.evaporation_mm,
                    )
                    finite_values = (cell.terrain.elevation_m, cell.atmosphere.temperature_c, *nonnegative_values)
                    if any(not math.isfinite(value) for value in finite_values) or any(value < 0.0 for value in nonnegative_values):
                        violations.append("planet contains invalid numeric state")
                        break
                    if not 0.0 <= cell.atmosphere.humidity <= 1.0:
                        violations.append("planet humidity outside [0,1]")
                        break
                    if not 0.0 <= cell.surface_water_quality <= 1.0 or cell.pollution < 0.0:
                        violations.append("planet water quality state invalid")
                        break

    if state.civilization.food.reserve < 0.0:
        violations.append("negative food reserve")
    if any(not 0.0 <= technology.progress <= 1.0 for technology in state.technologies.values()):
        violations.append("technology progress outside [0,1]")

    return InvariantReport(not violations, tuple(dict.fromkeys(violations)))
