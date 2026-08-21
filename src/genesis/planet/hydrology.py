from __future__ import annotations

from dataclasses import dataclass

from .terrain import TerrainCell


@dataclass(frozen=True, slots=True)
class HydrologyState:
    rainfall_mm: float
    runoff_mm: float
    infiltration_mm: float
    groundwater_mm: float
    river_flow: float
    lake_storage: float
    evaporation_mm: float

    def __post_init__(self) -> None:
        for value in (self.rainfall_mm, self.runoff_mm, self.infiltration_mm, self.groundwater_mm,
                      self.river_flow, self.lake_storage, self.evaporation_mm):
            if value < 0:
                raise ValueError("hydrology values cannot be negative")


@dataclass(frozen=True, slots=True)
class WaterRoute:
    x: int
    y: int
    downstream_x: int | None
    downstream_y: int | None
    path_length: int
    basin_id: str
    terminal: str


@dataclass(frozen=True, slots=True)
class BasinSummary:
    basin_id: str
    contributing_cells: int
    accumulated_runoff_mm: float
    terminal: str


class HydrologyEngine:
    """Water balance plus deterministic watershed, river and basin accumulation."""

    def __init__(self, infiltration_rate: float = 0.3, groundwater_recharge_rate: float = 0.25) -> None:
        if not 0 <= infiltration_rate <= 1 or not 0 <= groundwater_recharge_rate <= 1:
            raise ValueError("rates must be between 0 and 1")
        self.infiltration_rate = infiltration_rate
        self.groundwater_recharge_rate = groundwater_recharge_rate

    @staticmethod
    def evaporation(temperature_c: float, humidity: float, wind_mps: float) -> float:
        if not 0 <= humidity <= 1 or wind_mps < 0:
            raise ValueError("invalid atmospheric inputs")
        return max(0.0, (0.12 * max(0.0, temperature_c + 5.0)) * (1.0 - humidity) * (1.0 + 0.03 * wind_mps))

    def balance(self, *, rainfall_mm: float, temperature_c: float, humidity: float, wind_mps: float,
                soil_capacity_mm: float, surface_storage_mm: float) -> HydrologyState:
        if rainfall_mm < 0 or soil_capacity_mm < 0 or surface_storage_mm < 0:
            raise ValueError("water quantities cannot be negative")

        total_water = rainfall_mm + surface_storage_mm
        evaporation = min(total_water, self.evaporation(temperature_c, humidity, wind_mps))
        remaining = max(0.0, total_water - evaporation)
        infiltration = min(remaining * self.infiltration_rate, soil_capacity_mm)
        recharge = infiltration * self.groundwater_recharge_rate
        runoff = max(0.0, remaining - infiltration)
        river_flow = runoff
        lake = runoff
        return HydrologyState(
            rainfall_mm,
            runoff,
            infiltration,
            recharge,
            river_flow,
            lake,
            evaporation,
        )

    @staticmethod
    def downhill_neighbor(grid: tuple[tuple[TerrainCell, ...], ...], x: int, y: int) -> tuple[int, int] | None:
        height = len(grid)
        width = len(grid[0]) if height else 0
        if not (0 <= x < width and 0 <= y < height):
            raise IndexError("cell coordinates out of bounds")
        current = grid[y][x].elevation_m
        candidates: list[tuple[float, int, int]] = []
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < width and 0 <= ny < height and grid[ny][nx].elevation_m < current:
                candidates.append((grid[ny][nx].elevation_m, nx, ny))
        if not candidates:
            return None
        _, nx, ny = min(candidates)
        return nx, ny

    def route_water(self, grid: tuple[tuple[TerrainCell, ...], ...]) -> tuple[WaterRoute, ...]:
        routes: list[WaterRoute] = []
        cache: dict[tuple[int, int], tuple[str, int, str]] = {}
        height = len(grid)
        width = len(grid[0]) if height else 0

        def trace(start: tuple[int, int]) -> tuple[str, int, str]:
            if start in cache:
                return cache[start]
            path: list[tuple[int, int]] = []
            seen: set[tuple[int, int]] = set()
            current = start
            while True:
                if current in cache:
                    basin, depth, terminal = cache[current]
                    result = basin, len(path) + depth, terminal
                    break
                if current in seen:
                    result = f"closed:{current[0]}:{current[1]}", len(path) - 1, "closed_depression"
                    break
                seen.add(current)
                path.append(current)
                x, y = current
                if not grid[y][x].land:
                    result = f"ocean:{x}:{y}", len(path) - 1, "ocean"
                    break
                downstream = self.downhill_neighbor(grid, x, y)
                if downstream is None:
                    result = f"basin:{x}:{y}", len(path) - 1, "lake_or_watershed"
                    break
                current = downstream
            basin, depth, terminal = result
            for index, cell in enumerate(path):
                cache[cell] = (basin, max(0, depth - index), terminal)
            return result

        for y in range(height):
            for x in range(width):
                downstream = self.downhill_neighbor(grid, x, y) if grid[y][x].land else None
                basin, length, terminal = trace((x, y))
                routes.append(WaterRoute(x, y, downstream[0] if downstream else None,
                                         downstream[1] if downstream else None, length, basin, terminal))
        return tuple(routes)

    def aggregate_basins(self, routes: tuple[WaterRoute, ...], runoff_by_cell: dict[tuple[int, int], float]) -> tuple[BasinSummary, ...]:
        totals: dict[str, float] = {}
        counts: dict[str, int] = {}
        terminals: dict[str, str] = {}
        for route in routes:
            runoff = max(0.0, runoff_by_cell.get((route.x, route.y), 0.0))
            totals[route.basin_id] = totals.get(route.basin_id, 0.0) + runoff
            counts[route.basin_id] = counts.get(route.basin_id, 0) + 1
            terminals[route.basin_id] = route.terminal
        return tuple(
            BasinSummary(basin_id, counts[basin_id], totals[basin_id], terminals[basin_id])
            for basin_id in sorted(totals)
        )
