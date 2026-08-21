from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class OceanLayer:
    name: str
    depth_min_m: float
    depth_max_m: float
    temperature_c: float
    light: float
    oxygen: float
    nutrients: float
    biomass: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.depth_min_m < 0 or self.depth_max_m <= self.depth_min_m:
            raise ValueError("invalid ocean layer depth")
        if not 0 <= self.light <= 1 or not 0 <= self.oxygen <= 1 or self.nutrients < 0:
            raise ValueError("invalid ocean layer state")

    def primary_production(self) -> float:
        production = min(self.nutrients, self.light * self.oxygen * 0.25)
        self.biomass["phytoplankton"] = self.biomass.get("phytoplankton", 0.0) + production
        self.nutrients = max(0.0, self.nutrients - production * 0.4)
        return production

    def consumer_transfer(self) -> None:
        plankton = self.biomass.get("phytoplankton", 0.0)
        zooplankton = min(plankton, plankton * (0.65 if self.light > 0.05 else 0.25))
        self.biomass["zooplankton"] = self.biomass.get("zooplankton", 0.0) + zooplankton
        self.biomass["phytoplankton"] = max(0.0, plankton - zooplankton)
        fish = min(self.biomass["zooplankton"], zooplankton * 0.35)
        self.biomass["midwater_fish"] = self.biomass.get("midwater_fish", 0.0) + fish
        self.biomass["zooplankton"] = max(0.0, self.biomass["zooplankton"] - fish)
        apex = min(self.biomass["midwater_fish"], fish * 0.18)
        self.biomass["deep_predator"] = self.biomass.get("deep_predator", 0.0) + apex
        self.biomass["midwater_fish"] = max(0.0, self.biomass["midwater_fish"] - apex)


@dataclass(slots=True)
class OceanEcosystem:
    """Three-zone ocean ecology: photic, twilight and deep ocean."""

    layers: dict[str, OceanLayer]

    @classmethod
    def create(cls, surface_temperature_c: float, depth_m: float, nutrients: float = 1.0) -> "OceanEcosystem":
        depth = max(100.0, depth_m)
        layers = {
            "photic": OceanLayer("photic", 0, min(200.0, depth), surface_temperature_c, 0.9, 0.9, nutrients),
            "twilight": OceanLayer("twilight", 200.0, min(1000.0, max(250.0, depth)), surface_temperature_c - 5.0, 0.2, 0.8, nutrients * 1.2),
            "deep": OceanLayer("deep", min(1000.0, max(250.0, depth)), depth, surface_temperature_c - 15.0, 0.01, 0.65, nutrients * 2.0),
        }
        return cls(layers)

    def step(self) -> None:
        self.layers["photic"].primary_production()
        self.layers["twilight"].primary_production()
        self.layers["deep"].nutrients += self.layers["twilight"].biomass.get("zooplankton", 0.0) * 0.03
        for layer in self.layers.values():
            layer.consumer_transfer()
            detritus = sum(value for key, value in layer.biomass.items() if key not in {"phytoplankton", "zooplankton", "midwater_fish", "deep_predator"})
            layer.nutrients += detritus * 0.01
            layer.oxygen = max(0.0, layer.oxygen - detritus * 0.002)
