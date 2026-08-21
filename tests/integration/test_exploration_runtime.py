from genesis.life.animal import Animal, AnimalEcology
from genesis.planet.exploration_runtime import ExplorerState, ExplorationRuntime
from genesis.planet.terrain import TerrainGenerator, TerrainParams


def test_explorer_discovers_only_reachable_unknown_cells() -> None:
    terrain = TerrainGenerator(TerrainParams(width=8, height=8, seed=12)).generate()
    runtime = ExplorationRuntime()
    explorer = ExplorerState("human-1", 3, 3, movement_range=2)
    before = runtime.terrain_engine.knowledge_for("human-1")
    assert not before.is_known(3, 3)
    discoveries = runtime.explore(explorer, terrain, tick=5)
    assert discoveries
    assert all(runtime.terrain_engine.knowledge_for("human-1").is_known(d.x, d.y) for d in discoveries)


def test_animal_species_enters_human_knowledge_after_observation() -> None:
    runtime = ExplorationRuntime()
    animal = Animal("wolf-1", AnimalEcology(species_id="wolf"))
    first = runtime.observe_animal("human-1", animal, 10)
    second = runtime.observe_animal("human-1", animal, 11)
    assert first is not None
    assert first.known_by_society
    assert second is None
