from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from genesis.agriculture.farming import Farm
from genesis.agriculture.food import FoodBalance, FoodSystem
from genesis.planet.civilization_feedback import EnvironmentalImpact
from genesis.settlement.settlements import Settlement

if TYPE_CHECKING:
    from genesis.core.state import SimulationState


@dataclass(slots=True)
class CivilizationRuntime:
    """Authoritative bridge for human needs, food, settlements and environment feedback."""

    food: FoodSystem = field(default_factory=FoodSystem)
    farms: dict[str, Farm] = field(default_factory=dict)
    settlements: dict[str, Settlement] = field(default_factory=dict)
    agent_settlements: dict[str, str] = field(default_factory=dict)
    last_food_balance: FoodBalance | None = None
    food_enabled: bool = False

    def add_farm(self, farm: Farm) -> None:
        if farm.farm_id in self.farms:
            raise ValueError(f"farm already exists: {farm.farm_id}")
        self.farms[farm.farm_id] = farm
        self.food_enabled = True

    def add_settlement(self, settlement: Settlement) -> None:
        if settlement.settlement_id in self.settlements:
            raise ValueError(f"settlement already exists: {settlement.settlement_id}")
        self.settlements[settlement.settlement_id] = settlement

    def assign_agent(self, agent_id: str, settlement_id: str) -> None:
        if settlement_id not in self.settlements:
            raise ValueError(f"unknown settlement: {settlement_id}")
        previous = self.agent_settlements.get(agent_id)
        if previous == settlement_id:
            return
        if previous is not None and previous in self.settlements:
            self.settlements[previous].remove_resident(agent_id)
        self.agent_settlements[agent_id] = settlement_id
        self.settlements[settlement_id].add_resident(agent_id)

    def remove_agent(self, agent_id: str) -> None:
        settlement_id = self.agent_settlements.pop(agent_id, None)
        if settlement_id is not None and settlement_id in self.settlements:
            self.settlements[settlement_id].remove_resident(agent_id)

    def _rainfall_for_farm(self, farm: Farm, state: SimulationState) -> float:
        snapshot = state.planet_snapshot
        if snapshot is None or not snapshot.cells:
            return 0.0
        max_y = len(snapshot.cells) - 1
        max_x = len(snapshot.cells[0]) - 1
        x = max(0, min(max_x, farm.location[0]))
        y = max(0, min(max_y, farm.location[1]))
        precipitation = max(0.0, snapshot.cells[y][x].atmosphere.precipitation_mm)
        return min(0.25, precipitation / 1000.0)

    def _apply_food_effects(self, state: SimulationState, balance: FoodBalance, ticks: int) -> None:
        if not self.food_enabled:
            return
        alive_ids: list[str] = []
        for agent_id, agent in state.agents.items():
            person = state.demography.people.get(agent_id)
            health = state.health.states.get(agent_id)
            if person is not None and person.alive and health is not None and health.health > 0.0:
                alive_ids.append(agent_id)
        for agent_id in alive_ids:
            agent = state.agents[agent_id]
            if balance.security > 0.0:
                agent.needs.hunger = max(0.0, agent.needs.hunger - 0.10 * balance.security)
            if balance.starvation_pressure > 0.0:
                agent.needs.hunger = min(1.0, agent.needs.hunger + 0.05 * balance.starvation_pressure * ticks)
                health = state.health.states[agent_id]
                health.health = max(0.0, health.health - 0.01 * balance.starvation_pressure * ticks)

    def _reconcile_deaths(self, state: SimulationState) -> tuple[str, ...]:
        deaths: list[str] = []
        for agent_id, agent in state.agents.items():
            person = state.demography.people.get(agent_id)
            health = state.health.states.get(agent_id)
            if person is None or health is None:
                continue
            if health.health <= 0.0 and person.alive:
                person.alive = False
                deaths.append(agent_id)
            if not person.alive:
                agent.health = 0.0
                state.labor.fire(agent_id)
                self.remove_agent(agent_id)
        return tuple(deaths)

    def _advance_education(self, state: SimulationState, ticks: int) -> None:
        for (agent_id, course_id), record in tuple(state.education.students.items()):
            person = state.demography.people.get(agent_id)
            course = state.education.courses.get(course_id)
            if person is None or course is None or not person.alive or record.completed:
                continue
            record.study(ticks, course)
            if record.completed:
                agent = state.agents.get(agent_id)
                if agent is not None:
                    agent.skills[course.skill] = max(agent.skills.get(course.skill, 0.0), 1.0 - course.difficulty)

    def _upgrade_settlements(self) -> tuple[str, ...]:
        upgraded: list[str] = []
        for settlement_id, settlement in self.settlements.items():
            if settlement.auto_upgrade():
                upgraded.append(settlement_id)
        return tuple(upgraded)

    def derive_planetary_impacts(self, state: SimulationState) -> dict[tuple[int, int], EnvironmentalImpact]:
        population_by_cell: dict[tuple[int, int], int] = {}
        farmland_by_cell: dict[tuple[int, int], float] = {}
        for settlement in self.settlements.values():
            alive_population = sum(
                1
                for agent_id in settlement.population
                if state.demography.people.get(agent_id) is not None
                and state.demography.people[agent_id].alive
            )
            population_by_cell[settlement.location] = population_by_cell.get(settlement.location, 0) + alive_population
        for farm in self.farms.values():
            farmland_by_cell[farm.location] = farmland_by_cell.get(farm.location, 0.0) + farm.area

        impacts: dict[tuple[int, int], EnvironmentalImpact] = {}
        for key in population_by_cell.keys() | farmland_by_cell.keys():
            population = population_by_cell.get(key, 0)
            farmland = farmland_by_cell.get(key, 0.0)
            impacts[key] = EnvironmentalImpact(
                population_pressure=population / 1000.0,
                agriculture_pressure=farmland / 100.0,
                land_conversion=min(1.0, farmland / 100.0),
                water_extraction=0.0,
                pollution=0.0,
            )
        return impacts

    def step(self, state: SimulationState, ticks: int) -> tuple[tuple[str, ...], tuple[str, ...]]:
        if ticks < 0:
            raise ValueError("ticks cannot be negative")
        for farm in self.farms.values():
            farm.step(ticks, self._rainfall_for_farm(farm, state))

        alive_population = sum(
            1
            for agent_id in state.agents
            if state.demography.people.get(agent_id) is not None
            and state.demography.people[agent_id].alive
            and state.health.states.get(agent_id) is not None
            and state.health.states[agent_id].health > 0.0
        )
        if self.food_enabled:
            self.last_food_balance = self.food.step_from_farms(
                population=alive_population,
                farms=tuple(self.farms.values()),
            )
            self._apply_food_effects(state, self.last_food_balance, ticks)
        deaths = self._reconcile_deaths(state)
        self._advance_education(state, ticks)
        upgraded = self._upgrade_settlements()
        state.planet.set_civilization_impacts(self.derive_planetary_impacts(state))
        return deaths, upgraded
