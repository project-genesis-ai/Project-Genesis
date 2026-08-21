from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from .climate import ClimateCell, ClimateModel

if TYPE_CHECKING:
    from genesis.planet.coupling import PlanetSnapshot


class Biome(StrEnum):
    FOREST = "forest"
    GRASSLAND = "grassland"
    DESERT = "desert"
    WETLAND = "wetland"
    TUNDRA = "tundra"
    OCEAN = "ocean"


@dataclass(slots=True)
class EnvironmentCell:
    """Environmental mirror consumed by legacy life systems.

    Coordinates are optional for backwards compatibility; synchronized planetary
    cells always use their actual terrain coordinates.
    """

    cell_id: str
    biome: Biome
    elevation_m: float = 0.0
    temperature_c: float = 20.0
    rainfall_mm: float = 0.0
    water_mm: float = 0.0
    vegetation: float = 0.0
    x: int = 0
    y: int = 0

    def __post_init__(self) -> None:
        if not self.cell_id.strip():
            raise ValueError("cell_id cannot be empty")
        if not 0.0 <= self.vegetation <= 1.0:
            raise ValueError("vegetation must be between 0 and 1")
        if self.rainfall_mm < 0.0 or self.water_mm < 0.0:
            raise ValueError("water quantities cannot be negative")


@dataclass(slots=True)
class Environment:
    cells: dict[str, EnvironmentCell] = field(default_factory=dict)
    climate: dict[str, ClimateCell] = field(default_factory=dict)

    def add_cell(self, cell: EnvironmentCell) -> None:
        if cell.cell_id in self.cells:
            raise ValueError(f"Environment cell already exists: {cell.cell_id}")
        self.cells[cell.cell_id] = cell
        self.climate[cell.cell_id] = ClimateCell(temperature_c=cell.temperature_c)

    def cell(self, cell_id: str) -> EnvironmentCell:
        try:
            return self.cells[cell_id]
        except KeyError as exc:
            raise KeyError(f"Unknown environment cell: {cell_id}") from exc

    @staticmethod
    def _map_biome(name: str) -> Biome:
        if name in {"rainforest", "tropical_forest", "temperate_forest"}:
            return Biome.FOREST
        if name in {"tundra", "alpine_tundra", "boreal"}:
            return Biome.TUNDRA
        if name == "desert":
            return Biome.DESERT
        if name in {"wetland", "freshwater"}:
            return Biome.WETLAND
        if name == "ocean":
            return Biome.OCEAN
        return Biome.GRASSLAND

    def sync_from_planet(self, snapshot: PlanetSnapshot) -> None:
        """Mirror the authoritative planet snapshot for legacy life consumers."""
        expected: set[str] = set()
        for row in snapshot.cells:
            for state in row:
                cell = state.terrain
                cell_id = f"{cell.x}:{cell.y}"
                expected.add(cell_id)
                water = max(0.0, state.hydrology.groundwater_mm + state.hydrology.runoff_mm)
                vegetation = max(0.0, min(1.0, state.biome.vegetation_productivity))
                environment_cell = self.cells.get(cell_id)
                if environment_cell is None:
                    environment_cell = EnvironmentCell(
                        cell_id=cell_id,
                        biome=self._map_biome(state.biome.name),
                        elevation_m=cell.elevation_m,
                        temperature_c=state.atmosphere.temperature_c,
                        rainfall_mm=state.atmosphere.precipitation_mm,
                        water_mm=water,
                        vegetation=vegetation,
                        x=cell.x,
                        y=cell.y,
                    )
                    self.cells[cell_id] = environment_cell
                    self.climate[cell_id] = ClimateCell(temperature_c=environment_cell.temperature_c)
                else:
                    environment_cell.biome = self._map_biome(state.biome.name)
                    environment_cell.elevation_m = cell.elevation_m
                    environment_cell.temperature_c = state.atmosphere.temperature_c
                    environment_cell.rainfall_mm = state.atmosphere.precipitation_mm
                    environment_cell.water_mm = water
                    environment_cell.vegetation = vegetation
                    environment_cell.x = cell.x
                    environment_cell.y = cell.y
                    climate = self.climate.setdefault(cell_id, ClimateCell())
                    climate.temperature_c = environment_cell.temperature_c
                    climate.precipitation_mm = environment_cell.rainfall_mm
        stale = set(self.cells) - expected
        for cell_id in stale:
            self.cells.pop(cell_id, None)
            self.climate.pop(cell_id, None)

    def step_climate(self, tick: int, model: ClimateModel | None = None) -> None:
        climate_model = model or ClimateModel()
        for cell_id, climate in self.climate.items():
            climate_model.step(climate, tick)
            environment_cell = self.cells[cell_id]
            environment_cell.temperature_c = climate.temperature_c
            environment_cell.rainfall_mm = climate.precipitation_mm
            environment_cell.water_mm += climate.precipitation_mm
