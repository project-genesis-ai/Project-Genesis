from __future__ import annotations

from dataclasses import dataclass

from .exploration import Discovery, ExplorationEngine


@dataclass(frozen=True, slots=True)
class SpeciesDiscovery:
    explorer_id: str
    species_id: str
    tick: int
    known_by_society: bool


class SpeciesDiscoveryRegistry:
    """Tracks which species have entered human knowledge through direct observation."""

    def __init__(self) -> None:
        self.exploration = ExplorationEngine()
        self.known_species: set[str] = set()
        self.history: list[SpeciesDiscovery] = []

    def observe_species(self, explorer_id: str, species_id: str, tick: int) -> SpeciesDiscovery | None:
        if not explorer_id.strip() or not species_id.strip():
            raise ValueError("explorer and species identifiers cannot be empty")
        newly_known = species_id not in self.known_species
        if newly_known:
            self.known_species.add(species_id)
        event = SpeciesDiscovery(explorer_id, species_id, tick, newly_known)
        self.history.append(event)
        return event if newly_known else None
