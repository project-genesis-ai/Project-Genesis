from __future__ import annotations

from dataclasses import dataclass, field

from .civilization_feedback import EnvironmentalImpact
from .groundwater import GroundwaterEngine, GroundwaterState
from .hydrology import HydrologyState


@dataclass(frozen=True, slots=True)
class WaterCellRuntime:
    hydrology: HydrologyState
    groundwater: GroundwaterState
    pollution: float
    surface_water_quality: float


@dataclass(slots=True)
class HydrologyRuntime:
    """Persistent water-cycle state across simulation ticks."""

    groundwater: dict[tuple[int, int], GroundwaterState] = field(default_factory=dict)
    cells: dict[tuple[int, int], WaterCellRuntime] = field(default_factory=dict)
    groundwater_engine: GroundwaterEngine = field(default_factory=GroundwaterEngine)

    def step_cell(
        self,
        key: tuple[int, int],
        *,
        state: HydrologyState,
        civilization: EnvironmentalImpact | None = None,
    ) -> WaterCellRuntime:
        impact = civilization
        extraction = 0.0 if impact is None else max(0.0, impact.water_extraction)
        pollution = 0.0 if impact is None else max(0.0, impact.pollution)
        previous = self.groundwater.get(key, GroundwaterState())
        groundwater = self.groundwater_engine.step(
            previous,
            recharge_mm=state.groundwater_mm,
            aquifer_capacity_mm=250.0,
            demand_mm=extraction,
        )
        quality = max(0.0, min(1.0, 1.0 - pollution * 0.7 - extraction * 0.2))
        runtime = WaterCellRuntime(state, groundwater, pollution, quality)
        self.groundwater[key] = groundwater
        self.cells[key] = runtime
        return runtime
