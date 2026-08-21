from __future__ import annotations

from dataclasses import dataclass, field

from .civilization_feedback import EnvironmentalImpact
from .groundwater import GroundwaterEngine, GroundwaterState
from .hydrology import HydrologyState, WaterRoute


@dataclass(frozen=True, slots=True)
class WaterCellRuntime:
    """Persistent per-cell water state for one simulation tick."""

    hydrology: HydrologyState
    groundwater: GroundwaterState
    pollution: float
    surface_water_quality: float

    def __post_init__(self) -> None:
        if self.pollution < 0:
            raise ValueError("pollution cannot be negative")
        if not 0.0 <= self.surface_water_quality <= 1.0:
            raise ValueError("surface water quality must be between 0 and 1")


@dataclass(slots=True)
class HydrologyRuntime:
    """Persistent water-cycle state across planetary simulation ticks."""

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
        """Advance one cell while retaining its previous aquifer state."""
        if len(key) != 2:
            raise ValueError("water cell key must contain x and y")

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
        runtime = WaterCellRuntime(
            hydrology=state,
            groundwater=groundwater,
            pollution=pollution,
            surface_water_quality=quality,
        )
        self.groundwater[key] = groundwater
        self.cells[key] = runtime
        return runtime

    @staticmethod
    def route_runoff(
        routes: tuple[WaterRoute, ...],
        runoff_by_cell: dict[tuple[int, int], float],
    ) -> dict[tuple[int, int], float]:
        """Accumulate runoff downstream without mutating caller-owned input."""
        discharge = {
            (route.x, route.y): max(0.0, runoff_by_cell.get((route.x, route.y), 0.0))
            for route in routes
        }
        downstream = {
            (route.x, route.y): (
                (route.downstream_x, route.downstream_y)
                if route.downstream_x is not None and route.downstream_y is not None
                else None
            )
            for route in routes
        }

        # Water routes move strictly downhill, so larger path depths are upstream.
        for route in sorted(routes, key=lambda item: (-item.path_length, item.y, item.x)):
            target = downstream[(route.x, route.y)]
            if target is not None:
                discharge[target] = discharge.get(target, 0.0) + discharge[(route.x, route.y)]
        return discharge
