from __future__ import annotations

from typing import TYPE_CHECKING

from .behavior import EcologicalBehavior
from .ecosystem import Ecosystem
from .food_web import FoodWeb
from .forest import ForestDynamics
from .population import PopulationDynamics
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
    ) -> None:
        self.forest = forest or ForestDynamics()
        self.population = population or PopulationDynamics()
        self.behavior = behavior or EcologicalBehavior()
        self.food_web = food_web or FoodWeb()

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
        # PlanetEngine is authoritative whenever a snapshot is supplied. The
        # compatibility Environment is read-only for climate/forest purposes in
        # that mode so the legacy path cannot create a competing natural-world state.
        if planet_snapshot is None:
            environment.step_climate(simulation_tick)
            for cell in environment.cells.values():
                self.forest.step(cell, ticks)
        ecosystem.step(ticks)
        for organism in tuple(ecosystem.organisms.values()):
            if not organism.alive:
                continue
            self.behavior.forage(organism, self._habitat_for(environment, organism))
            prey = self.food_web.best_prey(ecosystem, organism)
            if prey is not None:
                self.food_web.feed(organism, prey)
        # Ecosystem owns biological reproduction. PopulationDynamics only
        # applies capacity/mortality here so one integrated tick cannot create
        # two births for the same parent.
        self.population.step(ecosystem, ticks, reproduce=False)

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
