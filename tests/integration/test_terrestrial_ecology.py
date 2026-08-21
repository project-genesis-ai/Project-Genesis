from genesis.planet.biome_dynamics import BiomassState, TerrestrialFoodWeb


def test_terrestrial_food_web_preserves_non_negative_biomass() -> None:
    state = BiomassState(100.0, 20.0, 5.0, 3.0, 2.0, 10.0)
    next_state = TerrestrialFoodWeb().step(state, productivity=0.8, moisture=0.7)
    assert min(next_state.plants, next_state.herbivores, next_state.predators, next_state.scavengers,
               next_state.decomposers, next_state.soil_organic_matter) >= 0
    assert next_state.plants > 0
