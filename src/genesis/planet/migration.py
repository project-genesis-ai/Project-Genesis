from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class MigrationIntent:
    organism_id: str
    target_x: int
    target_y: int
    urgency: float
    reason: str

    def __post_init__(self) -> None:
        if not self.organism_id.strip() or not self.reason.strip():
            raise ValueError("migration identifiers cannot be empty")
        if not 0 <= self.urgency <= 1:
            raise ValueError("urgency must be between 0 and 1")


class MigrationEngine:
    """Couples animal movement pressure to climate, water and food availability."""

    def intent(self, *, organism_id: str, x: int, y: int, candidates: tuple[dict[str, float], ...],
               temperature: float, preferred_temperature: float, water_need: float, local_water: float,
               food_need: float, local_food: float) -> MigrationIntent | None:
        if not candidates:
            return None
        heat_stress = min(1.0, abs(temperature - preferred_temperature) / 25.0)
        water_stress = min(1.0, max(0.0, water_need - local_water) / max(0.01, water_need))
        food_stress = min(1.0, max(0.0, food_need - local_food) / max(0.01, food_need))
        pressure = min(1.0, 0.45 * heat_stress + 0.3 * water_stress + 0.25 * food_stress)
        ranked: list[tuple[float, int, int, str]] = []
        for candidate in candidates:
            cx = int(candidate["x"])
            cy = int(candidate["y"])
            distance = math.hypot(cx - x, cy - y)
            suitability = candidate.get("food", 0.0) + candidate.get("water", 0.0) - candidate.get("climate_stress", 0.0)
            score = suitability - distance * 0.01
            ranked.append((-score, cx, cy, str(candidate.get("reason", "better_conditions"))))
        _, tx, ty, reason = min(ranked)
        if pressure < 0.2:
            return None
        return MigrationIntent(organism_id, tx, ty, pressure, reason)
