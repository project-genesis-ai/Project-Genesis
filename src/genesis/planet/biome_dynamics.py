from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BiomassState:
    plants: float
    herbivores: float
    predators: float
    scavengers: float
    decomposers: float
    soil_organic_matter: float


class TerrestrialFoodWeb:
    """Simple coupled biomass flow for the terrestrial trophic pyramid."""

    def step(self, state: BiomassState, *, productivity: float, moisture: float, disturbance: float = 0.0) -> BiomassState:
        if productivity < 0 or not 0 <= moisture <= 1 or disturbance < 0:
            raise ValueError("invalid ecological inputs")
        plant_growth = productivity * (0.15 + 0.35 * moisture) * max(0.0, 1.0 - disturbance)
        herbivore_gain = min(state.plants, state.plants * 0.08 * (0.4 + moisture))
        predator_gain = min(state.herbivores, state.herbivores * 0.06)
        scavenger_gain = min(state.herbivores + state.predators, (state.herbivores + state.predators) * 0.03)
        decomposition = (state.soil_organic_matter + state.scavengers * 0.04) * 0.05
        plants = max(0.0, state.plants + plant_growth - herbivore_gain + decomposition * 0.15)
        herbivores = max(0.0, state.herbivores + herbivore_gain - predator_gain - scavenger_gain * 0.4)
        predators = max(0.0, state.predators + predator_gain - scavenger_gain * 0.2)
        scavengers = max(0.0, state.scavengers + scavenger_gain - decomposition * 0.1)
        decomposers = max(0.0, state.decomposers + decomposition * 0.5 - decomposers_decay(state.decomposers))
        soil = max(0.0, state.soil_organic_matter + scavenger_gain + decomposition * 0.4 - herbivore_gain * 0.02)
        return BiomassState(plants, herbivores, predators, scavengers, decomposers, soil)


def decomposers_decay(value: float) -> float:
    return max(0.0, value * 0.02)
