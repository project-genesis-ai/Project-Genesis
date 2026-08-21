from genesis.planet.civilization import CivilizationCoupler, CivilizationKnowledge, SettlementSite
from genesis.planet.exploration import ExplorationKnowledge
from genesis.planet.terrain import TerrainCell
from genesis.planet.discovery import SpeciesDiscoveryRegistry


def test_unknown_regions_become_known_only_after_observation() -> None:
    knowledge = ExplorationKnowledge()
    cell = TerrainCell(3, 4, 120.0, True, 0.04)
    assert not knowledge.is_known(3, 4)
    discovery = knowledge.discover_cell("explorer-1", cell, 10)
    assert discovery.x == 3
    assert knowledge.is_known(3, 4)


def test_species_discovery_is_progressive() -> None:
    registry = SpeciesDiscoveryRegistry()
    first = registry.observe_species("explorer-1", "unknown-wolf", 12)
    second = registry.observe_species("explorer-1", "unknown-wolf", 13)
    assert first is not None
    assert first.known_by_society
    assert second is None


def test_civilization_uses_planetary_habitability_for_settlements() -> None:
    sites = (
        SettlementSite("A", 0, 0, 0.9, 0.9, 0.8, 200),
        SettlementSite("B", 1, 1, 0.2, 0.3, 0.2, 1000),
    )
    ranked = CivilizationCoupler().rank_settlement(sites)
    assert ranked[0].site_id == "A"
    knowledge = CivilizationKnowledge()
    exploration = ExplorationKnowledge()
    discovery = exploration.discover_cell("explorer-1", TerrainCell(0, 0, 100, True, 0.02), 20)
    CivilizationCoupler().apply_exploration(knowledge, (discovery,))
    assert (0, 0) in knowledge.known_regions
