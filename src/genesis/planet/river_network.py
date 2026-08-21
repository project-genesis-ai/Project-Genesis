from __future__ import annotations

from dataclasses import dataclass

from .hydrology import WaterRoute


@dataclass(frozen=True, slots=True)
class RiverSegment:
    x: int
    y: int
    downstream_x: int | None
    downstream_y: int | None
    discharge_mm: float
    order: int
    basin_id: str


@dataclass(frozen=True, slots=True)
class RiverNetwork:
    segments: tuple[RiverSegment, ...]
    lake_sinks: tuple[tuple[int, int], ...]


class RiverNetworkBuilder:
    """Accumulates runoff through route topology into stream/river discharge."""

    def build(self, routes: tuple[WaterRoute, ...], runoff_by_cell: dict[tuple[int, int], float]) -> RiverNetwork:
        discharge: dict[tuple[int, int], float] = {
            (route.x, route.y): max(0.0, runoff_by_cell.get((route.x, route.y), 0.0))
            for route in routes
        }
        downstream: dict[tuple[int, int], tuple[int, int] | None] = {
            (route.x, route.y): ((route.downstream_x, route.downstream_y) if route.downstream_x is not None and route.downstream_y is not None else None)
            for route in routes
        }

        # Process highest-route-depth cells first so upstream runoff reaches downstream segments.
        ordered = sorted(routes, key=lambda route: (-route.path_length, route.y, route.x))
        for route in ordered:
            target = downstream[(route.x, route.y)]
            if target is not None:
                discharge[target] = discharge.get(target, 0.0) + discharge[(route.x, route.y)]

        segments: list[RiverSegment] = []
        lake_sinks: list[tuple[int, int]] = []
        for route in routes:
            flow = discharge[(route.x, route.y)]
            if route.terminal in {"lake_or_watershed", "closed_depression"} and route.downstream_x is None:
                lake_sinks.append((route.x, route.y))
            segments.append(RiverSegment(
                x=route.x,
                y=route.y,
                downstream_x=route.downstream_x,
                downstream_y=route.downstream_y,
                discharge_mm=flow,
                order=max(1, int(flow ** 0.5)),
                basin_id=route.basin_id,
            ))
        return RiverNetwork(tuple(segments), tuple(sorted(set(lake_sinks))))
