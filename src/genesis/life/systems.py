from __future__ import annotations

from dataclasses import dataclass, replace
from math import hypot, ceil
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
        # PlanetEngine is authoritative whenever a snapshot is supplied. The
        # compatibility Environment is read-only for climate/forest purposes in
        # that mode so the legacy path cannot create a competing natural-world state.
        if planet_snapshot is None:
            environment.step_climate(simulation_tick)
            for cell in environment.cells.values():
                self.forest.step(cell, ticks)
        ecosystem.step(ticks)
        migrations: list[MigrationRecord] = []
        for organism in tuple(ecosystem.organisms.values()):
            if not organism.alive:
                continue
            self.behavior.forage(organism, self._habitat_for(environment, organism))
            prey = self.food_web.best_prey(ecosystem, organism)
            if prey is not None:
                self.food_web.feed(organism, prey)
            if planet_snapshot is not None and organism.species.migration_profile is not None:
                record = self._evaluate_migration(environment, organism)
                if record is not None:
                    organism.position = Vec3(float(record.destination[0]), organism.position.y, float(record.destination[1]))
                    migrations.append(record)
        # Ecosystem owns biological reproduction. PopulationDynamics only
        # applies capacity/mortality here so one integrated tick cannot create
        # two births for the same parent.
        self.population.step(ecosystem, ticks, reproduce=False)
        self.last_migrations = tuple(migrations)

    def _evaluate_migration(self, environment: Environment, organism):
        profile = organism.species.migration_profile
        if profile is None:
            return None
        x = round(organism.position.x)
        y = round(organism.position.z)
        source = self._nearest_environment_cell(environment, x, y)
        if source is None:
            return None
        current = self._conditions(source)
        radius = max(0, ceil(profile.maximum_daily_distance_km))
        candidates: dict[str, tuple[HabitatConditions, float, tuple[int, int]]] = {}
        for cell in environment.cells.values():
            distance = hypot(cell.x - x, cell.y - y)
            if distance <= 0.0 or distance > radius:
                continue
            candidates[cell.cell_id] = (self._conditions(cell), distance, (cell.x, cell.y))
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
    def _nearest_environment_cell(environment: Environment, x: int, y: int):
        if not environment.cells:
            return None
        return min(
            environment.cells.values(),
            key=lambda cell: ((cell.x - x) ** 2 + (cell.y - y) ** 2, cell.cell_id),
        )

    @staticmethod
    def _habitat_for(environment: Environment, organism):
        from .habitat import HabitatCell, HabitatMap

        habitat = HabitatMap()
        x = round(organism.position.x)
        y = round(organism.position.z)
        if not environment.cells:
            habitat.add(HabitatCell("default", x, y))
            return habitat

        source = min(
            environment.cells.values(),
            key=lambda cell: ((cell.x - x) ** 2 + (cell.y - y) ** 2, cell.cell_id),
        )
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
