from __future__ import annotations

from math import ceil, hypot
from typing import TYPE_CHECKING

from .behavior import EcologicalBehavior
from .ecosystem import Ecosystem
from .food_web import FoodWeb
from .forest import ForestDynamics
from .migration import HabitatConditions
from .population import PopulationDynamics
from genesis.physics.vectors import Vec3
from genesis.planet.migration_runtime import AnimalMigrationRuntime, MigrationRecord
from genesis.world.environment import Environment

if TYPE_CHECKING:
    from genesis.planet.coupling import PlanetSnapshot


class LifeSystem:
    """Coordinates compatibility life consumers over authoritative planetary conditions."""

    def __init__(
        self,
        forest: ForestDynamics | None = None,
        population: PopulationDynamics | None = None,
        behavior: EcologicalBehavior | None = None,
        food_web: FoodWeb | None = None,
        migration: AnimalMigrationRuntime | None = None,
    ) -> None:
        self.forest = forest or ForestDynamics()
        self.population = population or PopulationDynamics()
        self.behavior = behavior or EcologicalBehavior()
        self.food_web = food_web or FoodWeb()
        self.migration = migration or AnimalMigrationRuntime()
        self.last_migrations: tuple[MigrationRecord, ...] = ()

    def step(
        self,
        environment: Environment,
        ecosystem: Ecosystem,
        ticks: int,
        simulation_tick: int = 0,
        planet_snapshot: PlanetSnapshot | None = None,
    ) -> None:
        if ticks < 0:
            raise ValueError("ticks cannot be negative")
        self.last_migrations = ()
        if planet_snapshot is None:
            environment.step_climate(simulation_tick)
            for cell in environment.cells.values():
                self.forest.step(cell, ticks)
        cell_index = {(cell.x, cell.y): cell for cell in environment.cells.values()}
        ecosystem.step(ticks)
        migrations: list[MigrationRecord] = []
        for organism in tuple(ecosystem.organisms.values()):
            if not organism.alive:
                continue
            self.behavior.forage(organism, self._habitat_for(environment, organism, cell_index))
            prey = self.food_web.best_prey(ecosystem, organism)
            if prey is not None:
                self.food_web.feed(organism, prey)
            if planet_snapshot is not None and organism.species.migration_profile is not None:
                record = self._evaluate_migration(organism, cell_index)
                if record is not None:
                    organism.position = Vec3(float(record.destination[0]), organism.position.y, float(record.destination[1]))
                    migrations.append(record)
        self.population.step(ecosystem, ticks, reproduce=False)
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
        return HabitatConditions(
            temperature_c=cell.temperature_c,
            precipitation_mm=cell.rainfall_mm,
            water_availability=min(1.0, cell.water_mm / 100.0),
            food_availability=cell.vegetation,
            shelter_availability=min(1.0, 0.25 + cell.vegetation * 0.75),
        )

    @staticmethod
    def _nearest_environment_cell(x: int, y: int, cell_index):
        exact = cell_index.get((x, y))
        if exact is not None:
            return exact
        if not cell_index:
            return None
        return min(
            cell_index.values(),
            key=lambda cell: ((cell.x - x) ** 2 + (cell.y - y) ** 2, cell.cell_id),
        )

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

        habitat.add(
            HabitatCell(
                source.cell_id,
                x,
                y,
                biome=source.biome.value,
                vegetation=source.vegetation,
                water=min(1.0, source.water_mm / 100.0),
            )
        )
        return habitat
