from __future__ import annotations

from dataclasses import dataclass, field

from .farming import Farm, FarmState


@dataclass(frozen=True, slots=True)
class FoodBalance:
    """One settlement's food balance for a simulation tick."""

    population: int
    production: float
    demand: float
    consumed: float
    reserve: float
    deficit: float
    security: float
    starvation_pressure: float
    migration_pressure: float

    def __post_init__(self) -> None:
        if self.population < 0:
            raise ValueError("population cannot be negative")
        values = (
            self.production,
            self.demand,
            self.consumed,
            self.reserve,
            self.deficit,
            self.security,
            self.starvation_pressure,
            self.migration_pressure,
        )
        if any(value < 0 for value in values):
            raise ValueError("food balance values cannot be negative")
        if not all(0.0 <= value <= 1.0 for value in (self.security, self.starvation_pressure, self.migration_pressure)):
            raise ValueError("food pressure values must be between 0 and 1")


@dataclass(slots=True)
class FoodSystem:
    """Convert agricultural output into persistent food security signals.

    Farms remain the authoritative production source. The food system only
    aggregates harvests, applies spoilage, satisfies population demand and
    exposes shortage pressure for later demographic and migration decisions.
    """

    reserve: float = 0.0
    per_capita_demand: float = 1.0
    spoilage_rate: float = 0.02
    history: list[FoodBalance] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.reserve < 0 or self.per_capita_demand <= 0:
            raise ValueError("reserve must be non-negative and demand must be positive")
        if not 0.0 <= self.spoilage_rate < 1.0:
            raise ValueError("spoilage rate must be between 0 and 1")

    @staticmethod
    def harvest_ready(farms: tuple[Farm, ...]) -> float:
        """Harvest every ready farm exactly once and return raw food produced."""
        production = 0.0
        for farm in farms:
            if farm.state is FarmState.READY:
                production += farm.harvest()
        return production

    def step(self, *, population: int, production: float = 0.0) -> FoodBalance:
        if population < 0 or production < 0:
            raise ValueError("population and production cannot be negative")

        demand = population * self.per_capita_demand
        usable_production = production * (1.0 - self.spoilage_rate)
        available = self.reserve + usable_production
        consumed = min(available, demand)
        self.reserve = max(0.0, available - consumed)
        deficit = max(0.0, demand - consumed)
        security = 1.0 if demand == 0 else min(1.0, consumed / demand)
        starvation_pressure = 0.0 if demand == 0 else min(1.0, deficit / demand)
        migration_pressure = round(min(1.0, starvation_pressure * 0.8), 12)
        balance = FoodBalance(
            population=population,
            production=production,
            demand=demand,
            consumed=consumed,
            reserve=self.reserve,
            deficit=deficit,
            security=security,
            starvation_pressure=starvation_pressure,
            migration_pressure=migration_pressure,
        )
        self.history.append(balance)
        return balance

    def step_from_farms(self, *, population: int, farms: tuple[Farm, ...]) -> FoodBalance:
        """Harvest ready farms and immediately feed the settlement balance."""
        return self.step(population=population, production=self.harvest_ready(farms))
