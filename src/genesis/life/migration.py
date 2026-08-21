from __future__ import annotations

from dataclasses import dataclass
from math import hypot


@dataclass(frozen=True, slots=True)
class HabitatConditions:
    """Local environmental conditions relevant to seasonal animal movement."""

    temperature_c: float
    precipitation_mm: float
    water_availability: float
    food_availability: float
    shelter_availability: float

    def __post_init__(self) -> None:
        if min(self.precipitation_mm, self.water_availability, self.food_availability, self.shelter_availability) < 0:
            raise ValueError("habitat quantities cannot be negative")
        if max(self.water_availability, self.food_availability, self.shelter_availability) > 1:
            raise ValueError("habitat availability must be in [0,1]")


@dataclass(frozen=True, slots=True)
class MigrationProfile:
    """Species-level migration response, expressed as environmental optima and travel limits."""

    species_id: str
    migratory: bool
    preferred_temperature_c: float
    temperature_tolerance_c: float
    minimum_food: float = 0.25
    minimum_water: float = 0.25
    maximum_daily_distance_km: float = 25.0
    seasonal_sensitivity: float = 1.0

    def __post_init__(self) -> None:
        if self.temperature_tolerance_c <= 0 or self.maximum_daily_distance_km < 0:
            raise ValueError("migration limits must be positive")
        if not 0 <= self.minimum_food <= 1 or not 0 <= self.minimum_water <= 1:
            raise ValueError("resource thresholds must be in [0,1]")
        if self.seasonal_sensitivity < 0:
            raise ValueError("seasonal_sensitivity cannot be negative")


@dataclass(frozen=True, slots=True)
class MigrationDecision:
    should_migrate: bool
    destination_id: str | None
    reason: str
    suitability_current: float
    suitability_destination: float
    distance_km: float


def habitat_suitability(profile: MigrationProfile, conditions: HabitatConditions) -> float:
    thermal = max(0.0, 1.0 - abs(conditions.temperature_c - profile.preferred_temperature_c) / profile.temperature_tolerance_c)
    food = min(1.0, conditions.food_availability)
    water = min(1.0, conditions.water_availability)
    shelter = min(1.0, conditions.shelter_availability)
    return max(0.0, min(1.0, 0.40 * thermal + 0.30 * food + 0.20 * water + 0.10 * shelter))


def decide_migration(
    profile: MigrationProfile,
    current: HabitatConditions,
    candidates: dict[str, tuple[HabitatConditions, float]],
) -> MigrationDecision:
    current_score = habitat_suitability(profile, current)
    if not profile.migratory:
        return MigrationDecision(False, None, "species is non-migratory", current_score, current_score, 0.0)
    if not candidates:
        return MigrationDecision(False, None, "no reachable habitat", current_score, current_score, 0.0)

    best_id: str | None = None
    best_score = current_score
    best_distance = 0.0
    for destination_id, (conditions, distance_km) in candidates.items():
        if distance_km < 0 or distance_km > profile.maximum_daily_distance_km:
            continue
        score = habitat_suitability(profile, conditions)
        if conditions.food_availability < profile.minimum_food or conditions.water_availability < profile.minimum_water:
            continue
        if score > best_score:
            best_id, best_score, best_distance = destination_id, score, distance_km

    if best_id is None:
        return MigrationDecision(False, None, "current habitat remains preferable or safe route unavailable", current_score, current_score, 0.0)
    return MigrationDecision(True, best_id, "weather and resource conditions favor movement", current_score, best_score, best_distance)
