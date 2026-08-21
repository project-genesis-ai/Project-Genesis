from __future__ import annotations

from dataclasses import dataclass

from .atmosphere import AtmosphericState, AtmosphereEngine
from .biomes import BiomeEngine, BiomeState
from .hydrology import HydrologyEngine, HydrologyState, WaterRoute
from .terrain import TerrainCell, TerrainGenerator, TerrainParams


@dataclass(frozen=True, slots=True)
class PlanetCellState:
    terrain: TerrainCell
    atmosphere: AtmosphericState
    hydrology: HydrologyState
    biome: BiomeState


@dataclass(frozen=True, slots=True)
class PlanetSnapshot:
    cells: tuple[tuple[PlanetCellState, ...], ...]
    routes: tuple[WaterRoute, ...]
    tick: int


class PlanetEngine:
    """Coordinates terrain, atmosphere, hydrology and biome generation for one planet."""

    def __init__(self, terrain_params: TerrainParams = TerrainParams()) -> None:
        self.terrain_params = terrain_params
        self.terrain = TerrainGenerator(terrain_params)
        self.atmosphere = AtmosphereEngine()
        self.hydrology = HydrologyEngine()
        self.biomes = BiomeEngine()
        self._terrain_grid: tuple[tuple[TerrainCell, ...], ...] | None = None
        self._snapshot: PlanetSnapshot | None = None

    @property
    def snapshot(self) -> PlanetSnapshot | None:
        return self._snapshot

    def generate(self, tick: int = 0) -> tuple[tuple[PlanetCellState, ...], ...]:
        if tick < 0:
            raise ValueError("tick cannot be negative")
        terrain = self.terrain.generate()
        self._terrain_grid = terrain
        return self._build_snapshot(terrain, tick).cells

    def step(self, tick: int) -> PlanetSnapshot:
        if tick < 0:
            raise ValueError("tick cannot be negative")
        terrain = self._terrain_grid or self.terrain.generate()
        self._terrain_grid = terrain
        return self._build_snapshot(terrain, tick)

    def _build_snapshot(self, terrain: tuple[tuple[TerrainCell, ...], ...], tick: int) -> PlanetSnapshot:
        height = len(terrain)
        width = len(terrain[0]) if height else 0
        total_ocean = sum(1 for row in terrain for cell in row if not cell.land)
        ocean_fraction = total_ocean / max(1, width * height)
        states: list[list[PlanetCellState]] = []
        for y, row in enumerate(terrain):
            state_row: list[PlanetCellState] = []
            latitude = (y / max(1, height - 1) - 0.5) * 180.0
            for cell in row:
                base_moisture = 0.8 if not cell.land else 0.45
                atmosphere = self.atmosphere.state(
                    latitude=latitude,
                    elevation_m=cell.elevation_m,
                    tick=tick,
                    moisture=base_moisture,
                    ocean_fraction=ocean_fraction,
                )
                hydro = self.hydrology.balance(
                    rainfall_mm=atmosphere.precipitation_mm,
                    temperature_c=atmosphere.temperature_c,
                    humidity=atmosphere.humidity,
                    wind_mps=(atmosphere.wind_u_mps**2 + atmosphere.wind_v_mps**2) ** 0.5,
                    soil_capacity_mm=50.0 if cell.land else 0.0,
                    surface_storage_mm=0.0 if cell.land else 500.0,
                )
                biome = self.biomes.classify(
                    temperature_c=atmosphere.temperature_c,
                    precipitation_mm=atmosphere.precipitation_mm,
                    elevation_m=cell.elevation_m,
                    soil_moisture=min(1.0, hydro.groundwater_mm / 50.0),
                    freshwater=False,
                )
                state_row.append(PlanetCellState(cell, atmosphere, hydro, biome))
            states.append(state_row)
        snapshot = PlanetSnapshot(tuple(tuple(row) for row in states), self.hydrology.route_water(terrain), tick)
        self._snapshot = snapshot
        return snapshot
