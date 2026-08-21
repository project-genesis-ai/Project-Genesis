from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class NutrientPool:
    """Bounded soil nutrient pool used by producers and decomposers."""

    nitrogen: float = 1.0
    phosphorus: float = 1.0
    carbon: float = 1.0
    water: float = 1.0

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if min(self.nitrogen, self.phosphorus, self.carbon, self.water) < 0.0:
            raise ValueError("nutrient pools cannot be negative")

    def withdraw(self, nitrogen: float = 0.0, phosphorus: float = 0.0, carbon: float = 0.0, water: float = 0.0) -> None:
        amounts = (nitrogen, phosphorus, carbon, water)
        if min(amounts) < 0.0:
            raise ValueError("withdrawal cannot be negative")
        if nitrogen > self.nitrogen or phosphorus > self.phosphorus or carbon > self.carbon or water > self.water:
            raise ValueError("insufficient nutrients")
        self.nitrogen -= nitrogen
        self.phosphorus -= phosphorus
        self.carbon -= carbon
        self.water -= water

    def deposit(self, nitrogen: float = 0.0, phosphorus: float = 0.0, carbon: float = 0.0, water: float = 0.0) -> None:
        amounts = (nitrogen, phosphorus, carbon, water)
        if min(amounts) < 0.0:
            raise ValueError("deposit cannot be negative")
        self.nitrogen += nitrogen
        self.phosphorus += phosphorus
        self.carbon += carbon
        self.water += water


@dataclass(frozen=True, slots=True)
class EcologicalFlux:
    """One material flux between ecological pools."""

    nitrogen: float = 0.0
    phosphorus: float = 0.0
    carbon: float = 0.0
    water: float = 0.0

    def __post_init__(self) -> None:
        if min(self.nitrogen, self.phosphorus, self.carbon, self.water) < 0.0:
            raise ValueError("ecological flux cannot be negative")


@dataclass(slots=True)
class SoilSystem:
    """Simple mass-conserving decomposition and nutrient-recycling model."""

    pools: dict[str, NutrientPool] = field(default_factory=dict)
    litter: dict[str, EcologicalFlux] = field(default_factory=dict)

    def register(self, region_id: str, pool: NutrientPool | None = None) -> NutrientPool:
        if not region_id.strip():
            raise ValueError("region_id cannot be empty")
        if region_id in self.pools:
            raise ValueError(f"soil region already exists: {region_id}")
        value = pool or NutrientPool()
        self.pools[region_id] = value
        return value

    def add_litter(self, region_id: str, flux: EcologicalFlux) -> None:
        self._pool(region_id)
        old = self.litter.get(region_id, EcologicalFlux())
        self.litter[region_id] = EcologicalFlux(
            old.nitrogen + flux.nitrogen,
            old.phosphorus + flux.phosphorus,
            old.carbon + flux.carbon,
            old.water + flux.water,
        )

    def decompose(self, region_id: str, fraction: float = 0.1) -> EcologicalFlux:
        if not 0.0 <= fraction <= 1.0:
            raise ValueError("fraction must be between 0 and 1")
        self._pool(region_id)
        source = self.litter.get(region_id, EcologicalFlux())
        released = EcologicalFlux(source.nitrogen * fraction, source.phosphorus * fraction, source.carbon * fraction, source.water * fraction)
        remaining = EcologicalFlux(source.nitrogen - released.nitrogen, source.phosphorus - released.phosphorus, source.carbon - released.carbon, source.water - released.water)
        self.pools[region_id].deposit(released.nitrogen, released.phosphorus, released.carbon, released.water)
        self.litter[region_id] = remaining
        return released

    def _pool(self, region_id: str) -> NutrientPool:
        try:
            return self.pools[region_id]
        except KeyError as exc:
            raise KeyError(f"unknown soil region: {region_id}") from exc
