from __future__ import annotations

from dataclasses import dataclass, field

from .terrain import TerrainCell


@dataclass(frozen=True, slots=True)
class Discovery:
    explorer_id: str
    x: int
    y: int
    discovery_type: str
    value: str
    tick: int


@dataclass(slots=True)
class ExplorationKnowledge:
    explored: set[tuple[int, int]] = field(default_factory=set)
    discoveries: list[Discovery] = field(default_factory=list)

    def discover_cell(self, explorer_id: str, cell: TerrainCell, tick: int) -> Discovery:
        self.explored.add((cell.x, cell.y))
        if not cell.land:
            discovery_type = "ocean"
            value = "unknown ocean region"
        elif cell.elevation_m > 3000:
            discovery_type = "mountain"
            value = "high mountain region"
        elif cell.slope < 0.03:
            discovery_type = "plain"
            value = "open low-slope region"
        else:
            discovery_type = "terrain"
            value = "new landform"
        discovery = Discovery(explorer_id, cell.x, cell.y, discovery_type, value, tick)
        self.discoveries.append(discovery)
        return discovery

    def is_known(self, x: int, y: int) -> bool:
        return (x, y) in self.explored

    def newly_discovered_neighbors(self, x: int, y: int, radius: int = 1) -> tuple[tuple[int, int], ...]:
        if radius < 0:
            raise ValueError("radius cannot be negative")
        cells: list[tuple[int, int]] = []
        for nx in range(x - radius, x + radius + 1):
            for ny in range(y - radius, y + radius + 1):
                if (nx, ny) != (x, y) and (nx, ny) not in self.explored:
                    cells.append((nx, ny))
        return tuple(sorted(cells))


class ExplorationEngine:
    """Progressive discovery layer: agents only know terrain and ecology they have observed."""

    def __init__(self) -> None:
        self.knowledge: dict[str, ExplorationKnowledge] = {}

    def knowledge_for(self, explorer_id: str) -> ExplorationKnowledge:
        if not explorer_id.strip():
            raise ValueError("explorer_id cannot be empty")
        return self.knowledge.setdefault(explorer_id, ExplorationKnowledge())

    def observe(self, explorer_id: str, cells: tuple[TerrainCell, ...], tick: int) -> tuple[Discovery, ...]:
        knowledge = self.knowledge_for(explorer_id)
        return tuple(
            knowledge.discover_cell(explorer_id, cell, tick)
            for cell in sorted(cells, key=lambda item: (item.x, item.y))
            if not knowledge.is_known(cell.x, cell.y)
        )
