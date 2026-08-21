from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TransportMode(str, Enum):
    WALK = "walk"
    ANIMAL = "animal"
    CART = "cart"
    BOAT = "boat"
    RAIL = "rail"
    ROAD = "road"


@dataclass(frozen=True, slots=True)
class Road:
    road_id: str
    origin: str
    destination: str
    distance: float
    condition: float = 1.0
    mode: TransportMode = TransportMode.ROAD

    def __post_init__(self) -> None:
        if not self.road_id.strip() or not self.origin.strip() or not self.destination.strip() or self.distance <= 0:
            raise ValueError("invalid road")
        if not 0.0 <= self.condition <= 1.0:
            raise ValueError("condition must be between 0 and 1")

    @property
    def travel_time(self) -> float:
        speed = {TransportMode.WALK: 5.0, TransportMode.ANIMAL: 10.0, TransportMode.CART: 15.0, TransportMode.BOAT: 20.0, TransportMode.RAIL: 80.0, TransportMode.ROAD: 60.0}[self.mode]
        return self.distance / max(1.0, speed * (0.25 + 0.75 * self.condition))


@dataclass(slots=True)
class TransportNetwork:
    roads: dict[str, Road] = field(default_factory=dict)

    def add(self, road: Road) -> None:
        if road.road_id in self.roads:
            raise ValueError(f"road already exists: {road.road_id}")
        self.roads[road.road_id] = road

    def neighbors(self, location: str) -> tuple[Road, ...]:
        if not location.strip():
            raise ValueError("location cannot be empty")
        return tuple(road for road in self.roads.values() if road.origin == location or road.destination == location)

    def route_time(self, origin: str, destination: str) -> float | None:
        if origin == destination:
            return 0.0
        frontier: list[tuple[str, float]] = [(origin, 0.0)]
        best: dict[str, float] = {origin: 0.0}
        while frontier:
            frontier.sort(key=lambda item: item[1])
            current, elapsed = frontier.pop(0)
            if current == destination:
                return elapsed
            for road in self.neighbors(current):
                nxt = road.destination if road.origin == current else road.origin
                candidate = elapsed + road.travel_time
                if candidate < best.get(nxt, float("inf")):
                    best[nxt] = candidate
                    frontier.append((nxt, candidate))
        return None
