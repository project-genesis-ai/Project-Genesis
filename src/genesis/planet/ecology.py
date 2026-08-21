from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FoodWebLink:
    consumer: str
    resource: str
    transfer_efficiency: float = 0.1

    def __post_init__(self) -> None:
        if not self.consumer.strip() or not self.resource.strip():
            raise ValueError("food-web identifiers cannot be empty")
        if not 0 < self.transfer_efficiency <= 1:
            raise ValueError("transfer_efficiency must be in (0, 1]")


class FoodWeb:
    """Directed trophic network for terrestrial and aquatic ecosystems."""

    def __init__(self) -> None:
        self.links: set[FoodWebLink] = set()

    def add(self, link: FoodWebLink) -> None:
        self.links.add(link)

    def prey_of(self, consumer: str) -> tuple[str, ...]:
        return tuple(sorted(link.resource for link in self.links if link.consumer == consumer))

    def predators_of(self, resource: str) -> tuple[str, ...]:
        return tuple(sorted(link.consumer for link in self.links if link.resource == resource))

    def energy_available(self, *, biomass: float, consumed: float, efficiency: float = 0.1) -> float:
        if biomass < 0 or consumed < 0 or not 0 < efficiency <= 1:
            raise ValueError("invalid biomass or efficiency")
        return min(biomass, consumed) * efficiency

    def build_default_food_web(self) -> None:
        terrestrial = (
            ("herbivore", "plant"),
            ("small_predator", "herbivore"),
            ("apex_predator", "small_predator"),
            ("scavenger", "herbivore"),
            ("scavenger", "small_predator"),
            ("decomposer", "plant"),
            ("decomposer", "herbivore"),
            ("decomposer", "apex_predator"),
        )
        aquatic = (
            ("zooplankton", "phytoplankton"),
            ("small_fish", "zooplankton"),
            ("large_fish", "small_fish"),
            ("marine_predator", "large_fish"),
            ("marine_decomposer", "phytoplankton"),
            ("marine_decomposer", "small_fish"),
            ("marine_decomposer", "large_fish"),
        )
        for consumer, resource in terrestrial + aquatic:
            self.add(FoodWebLink(consumer, resource))
