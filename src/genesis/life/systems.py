from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil, hypot
from typing import TYPE_CHECKING

from .behavior import EcologicalBehavior
from .ecosystem import Ecosystem
from .food_web import FoodWeb
from .forest import ForestDynamics
from .frontier_evolution import EnvironmentalPressure
from .migration import HabitatConditions
from .population import PopulationDynamics
from genesis.physics.vectors import Vec3
from genesis.planet.migration_runtime import AnimalMigrationRuntime, MigrationRecord
from genesis.world.environment import Environment
from genesis.biology.dynamics import BiologicalDynamics, InfectionState
from genesis.biology.runtime import BiologicalStep, UniversalBiologyRuntime

if TYPE_CHECKING:
    from genesis.planet.coupling import PlanetSnapshot


@dataclass(slots=True)
class LifeSystem:
    """Coordinates the authoritative living ecosystem over planetary conditions."""

    forest: ForestDynamics = field(default_factory=ForestDynamics)
    population: PopulationDynamics = field(default_factory=PopulationDynamics)
    behavior: EcologicalBehavior = field(default_factory=EcologicalBehavior)
    food_web: FoodWeb = field(default_factory=FoodWeb)
    migration: AnimalMigrationRuntime = field(default_factory=AnimalMigrationRuntime)
    biology: UniversalBiologyRuntime = field(default_factory=UniversalBiologyRuntime)
    infection_clearance_rate: float = 0.05
    infections: dict[str, InfectionState] = field(default_factory=dict)
    last_migrations: tuple[MigrationRecord, ...] = ()
    last_biological_step: BiologicalStep = field(default_factory=lambda: BiologicalStep((), ()))
    last_infections: tuple[InfectionState, ...] = ()
    last_feeding: tuple[tuple[str, str, float], ...] = ()
    last_selection_pressure: dict[str, EnvironmentalPressure] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.infection_clearance_rate <= 1.0:
            raise ValueError("infection_clearance_rate must be between 0 and 1")

    def reseed(self, seed: int) -> None:
        self.population.seed = int(seed)
        self.population._rng.seed(int(seed))

    def seed_infection(self, host_id: str, pathogen_id: str = "environmental", load: float = 1.0, transmissibility: float = 0.1, damage: float = 0.05) -> InfectionState:
        if not host_id.strip() or not pathogen_id.strip():
            raise ValueError("host_id and pathogen_id cannot be empty")
        if load < 0.0 or not 0.0 <= transmissibility <= 1.0 or damage < 0.0:
            raise ValueError("invalid infection parameters")
        infection = InfectionState(pathogen_id, host_id, load, transmissibility, damage)
        self.infections[host_id] = infection
        return infection

    def _selection_pressures(self, environment: Environment, ecosystem: Ecosystem) -> dict[str, EnvironmentalPressure]:
        alive_by_species: dict[str, list] = {species_id: [] for species_id in ecosystem.species}
        for organism in ecosystem.organisms.values():
            if organism.alive:
                alive_by_species.setdefault(organism.species.species_id, []).append(organism)
        predator_counts: dict[str, int] = {species_id: 0 for species_id in ecosystem.species}
        for predator in ecosystem.species.values():
            for prey_species in predator.food_species:
                predator_counts[prey_species] = predator_counts.get(prey_species, 0) + ecosystem.population(predator.species_id)
        cell_index = {(cell.x, cell.y): cell for cell in environment.cells.values()}
        pressures: dict[str, EnvironmentalPressure] = {}
        for species_id, members in alive_by_species.items():
            if not members:
                continue
            population = len(members)
            food_scarcity = sum(1.0 - max(0.0, min(1.0, organism.energy)) for organism in members) / population
            predation = min(1.0, predator_counts.get(species_id, 0) / max(1, population))
            disease = sum(1 for organism in members if organism.organism_id in self.infections) / population
            temperature_values: list[float] = []
            water_values: list[float] = []
            for organism in members:
                source = self._nearest_environment_cell(round(organism.position.x), round(organism.position.z), cell_index)
                if source is None:
                    continue
                temperature_values.append(min(1.0, abs(source.temperature_c - 15.0) / 40.0))
                water_values.append(1.0 - min(1.0, source.water_mm / 100.0))
            temperature_stress = sum(temperature_values) / len(temperature_values) if temperature_values else 0.0
            water_scarcity = sum(water_values) / len(water_values) if water_values else 0.0
            pressures[species_id] = EnvironmentalPressure(food_scarcity, predation, disease, temperature_stress, water_scarcity)
        return pressures

    def _advance_disease(self, ecosystem: Ecosystem, seed: int) -> None:
        active: dict[str, InfectionState] = {}
        infected_ids = set(self.infections)
        for host_id in sorted(infected_ids):
            infection = self.infections[host_id]
            host = ecosystem.organisms.get(host_id)
            if host is None or not host.alive:
                continue
            BiologicalDynamics.apply_infection(host, infection)
            remaining_load = infection.load * (1.0 - self.infection_clearance_rate)
            if remaining_load > 1e-6:
                active[host_id] = InfectionState(infection.pathogen_id, host_id, remaining_load, infection.transmissibility, infection.damage)
        susceptible = sorted(organism.organism_id for organism in ecosystem.organisms.values() if organism.alive and organism.organism_id not in infected_ids)
        new_infections: list[InfectionState] = []
        for host_id in sorted(active):
            infection = active[host_id]
            for transmitted in BiologicalDynamics.transmit(infection, susceptible, seed):
                if transmitted.host_id not in active:
                    active[transmitted.host_id] = transmitted
                    new_infections.append(transmitted)
        self.infections = active
        self.last_infections = tuple(sorted(new_infections, key=lambda item: (item.pathogen_id, item.host_id)))

    def step(self, environment: Environment, ecosystem: Ecosystem, ticks: int, simulation_tick: int = 0, planet_snapshot: PlanetSnapshot | None = None) -> None:
        if ticks < 0:
            raise ValueError("ticks cannot be negative")
        self.last_migrations = ()
        self.last_infections = ()
        self.last_feeding = ()
        self.reseed(ecosystem.seed)
        if planet_snapshot is None:
            environment.step_climate(simulation_tick)
            for cell in environment.cells.values():
                self.forest.step(cell, ticks)
        else:
            for cell in environment.cells.values():
                if not environment.is_planet_managed(cell.cell_id):
                    self.forest.step(cell, ticks)
        self.last_biological_step = self.biology.step(environment, ecosystem, birth_tick=simulation_tick)
        cell_index = {(cell.x, cell.y): cell for cell in environment.cells.values()}
        self.last_selection_pressure = self._selection_pressures(environment, ecosystem)
        ecosystem.step(ticks, selection_pressure=self.last_selection_pressure)
        feeding: list[tuple[str, str, float]] = []
        migrations: list[MigrationRecord] = []
        for organism in tuple(sorted(ecosystem.organisms.values(), key=lambda item: item.organism_id)):
            if not organism.alive:
                continue
            self.behavior.forage(organism, self._habitat_for(environment, organism, cell_index))
            prey = self.food_web.best_prey(ecosystem, organism)
            if prey is not None:
                result = self.food_web.feed(organism, prey)
                if result is not None:
                    feeding.append((result.predator_id, result.prey_id, result.energy_transferred))
            if planet_snapshot is not None and organism.species.migration_profile is not None:
                record = self._evaluate_migration(organism, cell_index)
                if record is not None:
                    organism.position = Vec3(float(record.destination[0]), organism.position.y, float(record.destination[1]))
                    migrations.append(record)
        self.population.step(ecosystem, ticks, reproduce=False)
        self._advance_disease(ecosystem, seed=ecosystem.seed + simulation_tick)
        self.last_feeding = tuple(feeding)
        self.last_migrations = tuple(migrations)

    def _evaluate_migration(self, organism, cell_index):
        profile = organism.species.migration_profile
        if profile is None:
            return None
        x = round(organism.position.x)
        y = round(organism.position.z)
        source = self._nearest_environment_cell(x, y, cell_index)
        if source is None:
            return None
        current = self._conditions(source)
        radius = max(0, ceil(profile.maximum_daily_distance_km))
        candidates: dict[str, tuple[HabitatConditions, float, tuple[int, int]]] = {}
        for cy in range(y - radius, y + radius + 1):
            for cx in range(x - radius, x + radius + 1):
                cell = cell_index.get((cx, cy))
                if cell is None:
                    continue
                distance = hypot(cx - x, cy - y)
                if distance <= 0.0 or distance > profile.maximum_daily_distance_km:
                    continue
                candidates[cell.cell_id] = (self._conditions(cell), distance, (cx, cy))
        return self.migration.evaluate(organism, profile, current, candidates)

    @staticmethod
    def _conditions(cell) -> HabitatConditions:
        return HabitatConditions(temperature_c=cell.temperature_c, precipitation_mm=cell.rainfall_mm, water_availability=min(1.0, cell.water_mm / 100.0), food_availability=cell.vegetation, shelter_availability=min(1.0, 0.25 + cell.vegetation * 0.75))

    @staticmethod
    def _nearest_environment_cell(x: int, y: int, cell_index):
        exact = cell_index.get((x, y))
        if exact is not None:
            return exact
        if not cell_index:
            return None
        return min(cell_index.values(), key=lambda cell: ((cell.x - x) ** 2 + (cell.y - y) ** 2, cell.cell_id))

    @staticmethod
    def _habitat_for(environment: Environment, organism, cell_index):
        from .habitat import HabitatCell, HabitatMap
        habitat = HabitatMap()
        x = round(organism.position.x)
        y = round(organism.position.z)
        source = LifeSystem._nearest_environment_cell(x, y, cell_index)
        if source is None:
            habitat.add(HabitatCell("default", x, y))
            return habitat
        habitat.add(HabitatCell(source.cell_id, x, y, biome=source.biome.value, vegetation=source.vegetation, water=min(1.0, source.water_mm / 100.0)))
        return habitat
