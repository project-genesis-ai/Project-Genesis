from __future__ import annotations

from dataclasses import dataclass, field
import math

from genesis.life.animal import Animal
from .discovery import SpeciesDiscovery, SpeciesDiscoveryRegistry
from .exploration import Discovery, ExplorationEngine
from .terrain import TerrainCell


@dataclass(frozen=True, slots=True)
class ExplorerState:
    explorer_id: str
    x: int
    y: int
    movement_range: int = 1

    def __post_init__(self) -> None:
        if not self.explorer_id.strip() or self.movement_range < 0:
            raise ValueError("invalid explorer state")


@dataclass(slots=True)
class ExplorationRuntime:
    """Progressive map exploration and species observation for human agents."""

    terrain_engine: ExplorationEngine = field(default_factory=ExplorationEngine)
    species_registry: SpeciesDiscoveryRegistry = field(default_factory=SpeciesDiscoveryRegistry)

    def reachable_unknown_cells(self, explorer: ExplorerState, terrain: tuple[tuple[TerrainCell, ...], ...]) -> tuple[TerrainCell, ...]:
        height = len(terrain)
        width = len(terrain[0]) if height else 0
        knowledge = self.terrain_engine.knowledge_for(explorer.explorer_id)
        candidates: list[tuple[float, TerrainCell]] = []
        for y in range(max(0, explorer.y - explorer.movement_range), min(height, explorer.y + explorer.movement_range + 1)):
            for x in range(max(0, explorer.x - explorer.movement_range), min(width, explorer.x + explorer.movement_range + 1)):
                if knowledge.is_known(x, y):
                    continue
                distance = math.hypot(x - explorer.x, y - explorer.y)
                if distance <= explorer.movement_range:
                    candidates.append((distance, terrain[y][x]))
        candidates.sort(key=lambda item: (item[0], item[1].y, item[1].x))
        return tuple(cell for _, cell in candidates)

    def explore(self, explorer: ExplorerState, terrain: tuple[tuple[TerrainCell, ...], ...], tick: int) -> tuple[Discovery, ...]:
        cells = self.reachable_unknown_cells(explorer, terrain)
        return self.terrain_engine.observe(explorer.explorer_id, cells, tick)

    def observe_animal(self, explorer_id: str, animal: Animal, tick: int) -> SpeciesDiscovery | None:
        return self.species_registry.observe_species(explorer_id, animal.ecology.species_id, tick)
