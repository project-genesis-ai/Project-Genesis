from __future__ import annotations

from dataclasses import dataclass
from collections import deque

from .terrain import TerrainCell


@dataclass(frozen=True, slots=True)
class TerrainRegion:
    region_id: str
    kind: str
    area_cells: int
    cells: tuple[tuple[int, int], ...]
    min_elevation_m: float
    max_elevation_m: float
    mean_elevation_m: float
    mean_slope: float


@dataclass(frozen=True, slots=True)
class TerrainTopology:
    regions: tuple[TerrainRegion, ...]
    land_region_count: int
    ocean_region_count: int


class TerrainTopologyEngine:
    """Extracts continents, islands and ocean basins from generated terrain."""

    def build(self, grid: tuple[tuple[TerrainCell, ...], ...]) -> TerrainTopology:
        height = len(grid)
        width = len(grid[0]) if height else 0
        visited: set[tuple[int, int]] = set()
        regions: list[TerrainRegion] = []

        def neighbors(x: int, y: int) -> tuple[tuple[int, int], ...]:
            values: list[tuple[int, int]] = []
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < width and 0 <= ny < height:
                    values.append((nx, ny))
            return tuple(values)

        for y in range(height):
            for x in range(width):
                if (x, y) in visited:
                    continue
                is_land = grid[y][x].land
                queue: deque[tuple[int, int]] = deque([(x, y)])
                visited.add((x, y))
                cells: list[tuple[int, int]] = []
                while queue:
                    cx, cy = queue.popleft()
                    cells.append((cx, cy))
                    for nx, ny in neighbors(cx, cy):
                        if (nx, ny) in visited or grid[ny][nx].land != is_land:
                            continue
                        visited.add((nx, ny))
                        queue.append((nx, ny))
                samples = [grid[cy][cx] for cx, cy in cells]
                elevations = [cell.elevation_m for cell in samples]
                slopes = [cell.slope for cell in samples]
                if is_land:
                    kind = "island" if len(cells) < max(16, width * height // 100) else "continent"
                else:
                    kind = "ocean_basin"
                regions.append(TerrainRegion(
                    region_id=f"{kind}:{len(regions)}",
                    kind=kind,
                    area_cells=len(cells),
                    cells=tuple(cells),
                    min_elevation_m=min(elevations),
                    max_elevation_m=max(elevations),
                    mean_elevation_m=sum(elevations) / len(elevations),
                    mean_slope=sum(slopes) / len(slopes),
                ))
        regions.sort(key=lambda item: (-item.area_cells, item.region_id))
        land_count = sum(1 for region in regions if region.kind in {"continent", "island"})
        ocean_count = sum(1 for region in regions if region.kind == "ocean_basin")
        return TerrainTopology(tuple(regions), land_count, ocean_count)

    @staticmethod
    def local_extrema(grid: tuple[tuple[TerrainCell, ...], ...]) -> tuple[TerrainCell, ...]:
        """Identify coarse peaks and valley bottoms from immediate neighbors."""
        height = len(grid)
        width = len(grid[0]) if height else 0
        extrema: list[TerrainCell] = []
        for y in range(1, max(1, height - 1)):
            for x in range(1, max(1, width - 1)):
                cell = grid[y][x]
                neighbors = [grid[y - 1][x], grid[y + 1][x], grid[y][x - 1], grid[y][x + 1]]
                elevations = [neighbor.elevation_m for neighbor in neighbors]
                if cell.elevation_m >= max(elevations) or cell.elevation_m <= min(elevations):
                    extrema.append(cell)
        return tuple(extrema)
