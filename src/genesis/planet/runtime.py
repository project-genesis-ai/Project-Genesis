from __future__ import annotations

from dataclasses import dataclass, field

from genesis.life.ecosystem import Ecosystem
from genesis.life.organism import Organism
from .biome_dynamics import BiomassState, TerrestrialFoodWeb
from .coupling import PlanetSnapshot
from .civilization_feedback import PlanetaryCivilizationFeedback


@dataclass(slots=True)
class PlanetEcologyRuntime:
    """Applies planetary habitat conditions to organism survival and biomass dynamics."""

    food_web: TerrestrialFoodWeb = field(default_factory=TerrestrialFoodWeb)
    civilization_feedback: PlanetaryCivilizationFeedback = field(default_factory=PlanetaryCivilizationFeedback)
    terrestrial_biomass: dict[str, BiomassState] = field(default_factory=dict)

    def habitat_stress(self, snapshot: PlanetSnapshot, organism: Organism) -> float:
        if not snapshot.cells:
            return 0.0
        x = max(0, min(snapshot.cells[0][0].terrain.x, round(organism.position.x)))
        y = max(0, min(snapshot.cells[0][0].terrain.y, round(organism.position.z)))
        try:
            cell = snapshot.cells[y][x]
        except IndexError:
            cell = snapshot.cells[0][0]
        temp_optimum = 15.0
        temperature_stress = min(1.0, abs(cell.atmosphere.temperature_c - temp_optimum) / 35.0)
        water_stress = max(0.0, 0.5 - min(1.0, cell.hydrology.groundwater_mm / 50.0))
        productivity_stress = max(0.0, 0.55 - cell.biome.vegetation_productivity)
        return min(1.0, 0.5 * temperature_stress + 0.3 * water_stress + 0.2 * productivity_stress)

    def step_terrestrial_biomass(self, biome_name: str, *, productivity: float, moisture: float, disturbance: float = 0.0) -> BiomassState:
        previous = self.terrestrial_biomass.get(
            biome_name,
            BiomassState(plants=1.0, herbivores=0.25, predators=0.06, scavengers=0.03, decomposers=0.02, soil_organic_matter=0.15),
        )
        next_state = self.food_web.step(previous, productivity=productivity, moisture=moisture, disturbance=disturbance)
        self.terrestrial_biomass[biome_name] = next_state
        return next_state

    def apply_to_ecosystem(self, ecosystem: Ecosystem, snapshot: PlanetSnapshot) -> None:
        """Apply current planetary stress to all living organisms before ecological reproduction."""
        for organism in ecosystem.organisms.values():
            if not organism.alive:
                continue
            stress = self.habitat_stress(snapshot, organism)
            organism.survive(stress)
