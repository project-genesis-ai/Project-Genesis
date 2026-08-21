from __future__ import annotations

from dataclasses import dataclass, field

from .discovery import SpeciesDiscovery
from .exploration import Discovery


@dataclass(slots=True)
class SettlementSite:
    site_id: str
    x: int
    y: int
    water_access: float
    food_potential: float
    fertility: float
    elevation_m: float
    population: int = 0

    @property
    def habitability(self) -> float:
        return max(0.0, min(1.0, 0.35 * self.water_access + 0.3 * self.food_potential + 0.25 * self.fertility + 0.1 * max(0.0, 1.0 - abs(self.elevation_m) / 5000.0)))


@dataclass(slots=True)
class CivilizationKnowledge:
    known_regions: set[tuple[int, int]] = field(default_factory=set)
    known_species: set[str] = field(default_factory=set)
    discovered_resources: set[str] = field(default_factory=set)

    def ingest_discovery(self, discovery: Discovery) -> None:
        self.known_regions.add((discovery.x, discovery.y))
        if discovery.discovery_type in {"mountain", "plain", "terrain", "ocean"}:
            self.discovered_resources.add(discovery.discovery_type)

    def ingest_species(self, event: SpeciesDiscovery) -> None:
        self.known_species.add(event.species_id)


class CivilizationCoupler:
    """Turns planetary conditions and exploration knowledge into settlement inputs."""

    def rank_settlement(self, sites: tuple[SettlementSite, ...]) -> tuple[SettlementSite, ...]:
        return tuple(sorted(sites, key=lambda site: (-site.habitability, site.site_id)))

    def apply_exploration(self, knowledge: CivilizationKnowledge, discoveries: tuple[Discovery, ...]) -> None:
        for discovery in discoveries:
            knowledge.ingest_discovery(discovery)

    def apply_species_discovery(self, knowledge: CivilizationKnowledge, events: tuple[SpeciesDiscovery, ...]) -> None:
        for event in events:
            if event.known_by_society:
                knowledge.ingest_species(event)
