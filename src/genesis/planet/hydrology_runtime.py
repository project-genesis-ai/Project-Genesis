from __future__ import annotations

from dataclasses import dataclass, field

from .civilization_feedback import EnvironmentalImpact
from .groundwater import GroundwaterEngine, GroundwaterState
from .hydrology import HydrologyEngine, HydrologyState, WaterRoute


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
    engine: HydrologyEngine = field(default_factory=HydrologyEngine)
    groundwater_engine: GroundwaterEngine = field(default_factory=GroundwaterEngine)

    def step_cell(self, key: tuple[int, int], *, state: HydrologyState, civilization: EnvironmentalImpact | None = None) -> WaterCellRuntime:
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

    @staticmethod
    def route_runoff(routes: tuple[WaterRoute, ...], runoff: dict[tuple[int, int], float]) -> dict[tuple[int, int], float]:
        discharge = {key: max(0.0, value) for key, value in runoff.items()}
        ordered = sorted(routes, key=lambda route: (-route.path_length, route.y, route.x))
        for route in ordered:
            source = (route.x, route.y)
            if route.downstream_x is not None and route.downstream_y is not None:
                target = (route.downstream_x, route.downstream_y)
                discharge[target] = discharge.get(target, 0.0) + discharge.get(source, 0.0)
        return discharge
