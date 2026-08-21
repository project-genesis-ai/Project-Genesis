from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from genesis.education.education import Course
from genesis.events.event import SimulationEvent

if TYPE_CHECKING:
    from genesis.core.simulation import Simulation
    from genesis.core.state import SimulationState


@dataclass(slots=True)
class CivilizationAutonomy:
    """Connects human movement, work, education and civic finance into the main tick loop."""

    movement_per_tick: int = 1
    default_tax_rate: float = 0.05

    def _bounds(self, state: SimulationState) -> tuple[int, int]:
        snapshot = state.planet_snapshot
        if snapshot is None or not snapshot.cells:
            return 0, 0
        return len(snapshot.cells[0]) - 1, len(snapshot.cells) - 1

    def _move(self, state: SimulationState, simulation: Simulation) -> None:
        max_x, max_y = self._bounds(state)
        if max_x <= 0 or max_y <= 0:
            return
        for agent_id, agent in sorted(state.agents.items()):
            if agent.health <= 0.0:
                continue
            target: tuple[int, int] | None = None
            settlement_id = state.civilization.agent_settlements.get(agent_id)
            if settlement_id is not None:
                settlement = state.civilization.settlements.get(settlement_id)
                if settlement is not None:
                    target = settlement.location
            if target is None:
                knowledge = state.exploration.terrain_engine.knowledge.get(agent_id)
                if knowledge is not None and knowledge.discoveries:
                    last = knowledge.discoveries[-1]
                    target = (last.x, last.y)
            if target is None:
                continue
            tx, ty = target
            dx = 0 if tx == agent.world_x else (1 if tx > agent.world_x else -1)
            dy = 0 if ty == agent.world_y else (1 if ty > agent.world_y else -1)
            new_x = max(0, min(max_x, agent.world_x + dx * self.movement_per_tick))
            new_y = max(0, min(max_y, agent.world_y + dy * self.movement_per_tick))
            if (new_x, new_y) != (agent.world_x, agent.world_y):
                before = (agent.world_x, agent.world_y)
                agent.move_world(new_x, new_y)
                simulation.emit(SimulationEvent(simulation.time.tick, "HumanMoved", actor_id=agent_id, data={"from": before, "to": (new_x, new_y)}))

    def _ensure_courses(self, state: SimulationState) -> None:
        if state.education.courses:
            return
        defaults = (
            Course("basic-literacy", "literacy", "literacy", 40, 0.15),
            Course("basic-numeracy", "numeracy", "numeracy", 50, 0.20),
            Course("agriculture", "agriculture", "agriculture", 60, 0.35),
            Course("craft", "engineering", "engineering", 80, 0.45),
            Course("science", "science", "science", 100, 0.60),
        )
        for course in defaults:
            state.education.add_course(course)

    def _education(self, state: SimulationState) -> None:
        self._ensure_courses(state)
        for agent_id, agent in sorted(state.agents.items()):
            person = state.demography.people.get(agent_id)
            if person is None or not person.alive or agent.health <= 0.0:
                continue
            preferred = "science" if agent.age_ticks >= 18000 else "agriculture" if agent.age_ticks >= 8000 else "basic-literacy"
            course_id = next((course_id for course_id, course in state.education.courses.items() if course.skill == preferred), "basic-literacy")
            record = state.education.enroll(agent_id, course_id)
            if not record.completed:
                agent.knowledge.add(f"education:{preferred}")

    def _labor(self, state: SimulationState) -> None:
        jobs = tuple(sorted(state.labor.jobs.values(), key=lambda job: (-job.wage_per_tick, job.job_id)))
        if not jobs:
            return
        for agent_id, agent in sorted(state.agents.items()):
            person = state.demography.people.get(agent_id)
            if person is None or not person.alive or agent.health <= 0.0 or agent_id in state.labor.workers:
                continue
            preferred = max(agent.skills, key=agent.skills.get) if agent.skills else "general"
            matching = [job for job in jobs if job.skill == preferred]
            job = (matching or list(jobs))[0]
            if state.labor.hire(agent_id, job.job_id):
                agent.skills.setdefault(job.skill, 0.1)

    def _civic_finance(self, state: SimulationState, simulation: Simulation, ticks: int) -> None:
        for government_id, government in sorted(state.governments.items()):
            citizens = tuple(agent_id for agent_id in government.population if agent_id in state.agents)
            if not citizens:
                continue
            tax_rate = min(0.25, max(0.0, government.laws.get("income_tax", self.default_tax_rate)))
            collected = 0.0
            for agent_id in sorted(citizens):
                wallet = state.wallets.get(agent_id)
                if wallet is None:
                    continue
                tax = min(wallet.balance, wallet.balance * tax_rate * ticks)
                if tax > 0.0 and wallet.debit(tax):
                    collected += tax
                    state.ledger.transfer(f"tax:{simulation.time.tick}:{government_id}:{agent_id}", simulation.time.tick, f"wallet:{agent_id}", f"government:{government_id}", tax, "income tax")
                    simulation.emit(SimulationEvent(simulation.time.tick, "TaxPaid", actor_id=agent_id, target_id=government_id, data={"amount": tax}))
            if collected:
                government.collect_tax(collected)
            per_capita = government.treasury / max(1, len(citizens))
            service_budget = min(government.treasury, per_capita * 0.01 * len(citizens))
            if service_budget > 0.0:
                government.spend("public_services", service_budget)

    def step(self, state: SimulationState, simulation: Simulation, ticks: int) -> None:
        if ticks < 0:
            raise ValueError("ticks cannot be negative")
        self._move(state, simulation)
        self._education(state)
        self._labor(state)
        self._civic_finance(state, simulation, ticks)
