from genesis.life.species_presets import forest_species
from genesis.physics.body import Body
from genesis.physics.vectors import Vec3
from genesis.world.environment import Biome, EnvironmentCell
from genesis.core.simulation import Simulation


def test_natural_world_components_advance_together() -> None:
    simulation = Simulation()
    simulation.state.environment.add_cell(
        EnvironmentCell("forest-1", Biome.FOREST, temperature_c=24.0, water_mm=10.0, vegetation=0.2)
    )
    for species in forest_species():
        simulation.state.ecosystem.register_species(species)
    simulation.state.physics.add_body(Body("planet-a", 1.0, position=Vec3(-1.0, 0.0, 0.0)))
    simulation.state.physics.add_body(Body("planet-b", 1.0, position=Vec3(1.0, 0.0, 0.0)))

    simulation.step()

    assert simulation.state.environment.cell("forest-1").vegetation > 0.2
    assert simulation.state.physics.bodies["planet-a"].velocity_mps.x > 0.0
    assert simulation.time.tick == 1
