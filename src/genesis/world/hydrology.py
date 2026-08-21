from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WaterFlux:
    rainfall_mm: float = 0.0
    runoff_mm: float = 0.0
    infiltration_mm: float = 0.0
    evaporation_mm: float = 0.0

    def __post_init__(self) -> None:
        if min(self.rainfall_mm, self.runoff_mm, self.infiltration_mm, self.evaporation_mm) < 0:
            raise ValueError("water flux values cannot be negative")


@dataclass(slots=True)
class WatershedCell:
    cell_id: str
    elevation_m: float
    area_km2: float
    rainfall_mm: float
    soil_infiltration_fraction: float = 0.3
    groundwater_mm: float = 0.0
    surface_water_mm: float = 0.0
    downstream_id: str | None = None

    def __post_init__(self) -> None:
        if self.area_km2 <= 0 or self.rainfall_mm < 0 or self.elevation_m < -10000:
            raise ValueError("invalid watershed cell")
        if not 0 <= self.soil_infiltration_fraction <= 1:
            raise ValueError("infiltration fraction must be in [0,1]")

    def water_balance(self, evaporation_mm: float = 0.0) -> WaterFlux:
        if evaporation_mm < 0:
            raise ValueError("evaporation cannot be negative")
        available = max(0.0, self.rainfall_mm - evaporation_mm)
        infiltration = available * self.soil_infiltration_fraction
        runoff = available - infiltration
        self.groundwater_mm += infiltration
        self.surface_water_mm += runoff
        return WaterFlux(self.rainfall_mm, runoff, infiltration, evaporation_mm)


@dataclass(slots=True)
class HydrologicalNetwork:
    cells: dict[str, WatershedCell]

    def route_runoff(self) -> dict[str, float]:
        flow: dict[str, float] = {}
        ordered = sorted(self.cells.values(), key=lambda c: c.elevation_m, reverse=True)
        for cell in ordered:
            amount = cell.surface_water_mm
            cell.surface_water_mm = 0.0
            if cell.downstream_id is None:
                flow[cell.cell_id] = flow.get(cell.cell_id, 0.0) + amount
            else:
                downstream = self.cells.get(cell.downstream_id)
                if downstream is None:
                    raise KeyError(f"unknown downstream cell: {cell.downstream_id}")
                downstream.surface_water_mm += amount
                flow[cell.downstream_id] = flow.get(cell.downstream_id, 0.0) + amount
        return flow

    def cycle(self, evaporation_mm: float = 0.0) -> dict[str, WaterFlux]:
        fluxes = {cell.cell_id: cell.water_balance(evaporation_mm) for cell in self.cells.values()}
        self.route_runoff()
        return fluxes
