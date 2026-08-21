from __future__ import annotations

from .behavior import EcologicalBehavior
from .ecosystem import Ecosystem
from .food_web import FoodWeb
from .forest import ForestDynamics
from .population import PopulationDynamics
from genesis.world.environment import Environment


class LifeSystem:
    """Coordinates environment, vegetation, organisms, trophic interactions, and births."""

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

    def step(self, environment: Environment, ecosystem: Ecosystem, ticks: int, simulation_tick: int = 0) -> None:
        if ticks < 0:
            raise ValueError("ticks cannot be negative")
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
        self.population.step(ecosystem, ticks)

    @staticmethod
    def _habitat_for(environment: Environment, organism):
        from .habitat import HabitatCell, HabitatMap

        habitat = HabitatMap()
        x = round(organism.position.x)
        y = round(organism.position.y)
        cell_id = next(iter(environment.cells), "default")
        source = environment.cells.get(cell_id)
        if source is None:
            habitat.add(HabitatCell("default", x, y))
        else:
            habitat.add(HabitatCell(cell_id, x, y, biome=source.biome.value, vegetation=source.vegetation, water=min(1.0, source.water_mm / 100.0)))
        return habitat
