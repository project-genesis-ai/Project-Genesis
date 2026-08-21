from __future__ import annotations

from dataclasses import dataclass, field

from genesis.physics import Energy

@dataclass(slots=True)
class UtilityNode:
    node_id: str
    population: int = 0
    water_m3: float = 0.0
    electricity: Energy = field(default_factory=lambda: Energy(0.0))

    def __post_init__(self) -> None:
        if not self.node_id.strip() or self.population < 0 or self.water_m3 < 0:
            raise ValueError("invalid utility node")

    def consume_water(self, litres_per_person_day: float, days: float = 1.0) -> float:
        if litres_per_person_day < 0 or days < 0:
            raise ValueError("utility demand cannot be negative")
        demand_m3 = self.population * litres_per_person_day * days / 1000.0
        consumed = min(self.water_m3, demand_m3)
        self.water_m3 -= consumed
        return consumed

    def consume_electricity(self, power_watts: float, seconds: float) -> Energy:
        if power_watts < 0 or seconds < 0:
            raise ValueError("electricity demand cannot be negative")
        demand = Energy(power_watts * seconds)
        consumed = min(self.electricity.joules, demand.joules)
        self.electricity = Energy(self.electricity.joules - consumed)
        return Energy(consumed)

@dataclass(slots=True)
class UtilityNetwork:
    nodes: dict[str, UtilityNode] = field(default_factory=dict)

    def add(self, node: UtilityNode) -> None:
        if node.node_id in self.nodes:
            raise ValueError(f"utility node already exists: {node.node_id}")
        self.nodes[node.node_id] = node

    def total_water_m3(self) -> float:
        return sum(node.water_m3 for node in self.nodes.values())

    def total_electricity(self) -> Energy:
        return Energy(sum(node.electricity.joules for node in self.nodes.values()))
