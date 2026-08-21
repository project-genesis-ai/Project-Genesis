from __future__ import annotations

from dataclasses import dataclass, field

from genesis.agriculture.farming import Farm


@dataclass(frozen=True, slots=True)
class EnvironmentalImpact:
    population_pressure: float
    agriculture_pressure: float
    land_conversion: float
    water_extraction: float
    pollution: float

    def __post_init__(self) -> None:
        for value in (self.population_pressure, self.agriculture_pressure, self.land_conversion,
                      self.water_extraction, self.pollution):
            if value < 0:
                raise ValueError("environmental impact values cannot be negative")


@dataclass(slots=True)
class PlanetaryCivilizationFeedback:
    """Maps civilization activity into ecological pressure while retaining explicit state."""

    impacts: dict[str, EnvironmentalImpact] = field(default_factory=dict)

    def assess(self, *, region_id: str, population: int, farmland_area: float,
               water_extraction: float, pollution: float, natural_land_area: float) -> EnvironmentalImpact:
        if not region_id.strip() or population < 0 or farmland_area < 0 or water_extraction < 0 or pollution < 0 or natural_land_area < 0:
            raise ValueError("invalid civilization impact inputs")
        pressure = population / max(1.0, natural_land_area * 1000.0)
        agriculture = farmland_area / max(1.0, natural_land_area)
        land_conversion = min(1.0, agriculture)
        impact = EnvironmentalImpact(
            population_pressure=pressure,
            agriculture_pressure=agriculture,
            land_conversion=land_conversion,
            water_extraction=water_extraction,
            pollution=pollution,
        )
        self.impacts[region_id] = impact
        return impact

    @staticmethod
    def farm_pressure(farms: tuple[Farm, ...]) -> float:
        if not farms:
            return 0.0
        return sum(max(0.0, farm.area) for farm in farms)

    def climate_pressure(self, region_id: str) -> float:
        impact = self.impacts.get(region_id)
        if impact is None:
            return 0.0
        return min(1.0, (
            impact.population_pressure * 0.15
            + impact.agriculture_pressure * 0.30
            + impact.water_extraction * 0.25
            + impact.pollution * 0.30
        ))
