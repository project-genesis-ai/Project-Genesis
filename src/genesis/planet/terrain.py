from __future__ import annotations

from dataclasses import dataclass
import math
import random


@dataclass(frozen=True, slots=True)
class TerrainParams:
    width: int = 128
    height: int = 128
    seed: int = 0
    ocean_fraction: float = 0.62
    mountain_strength: float = 0.35
    island_strength: float = 0.18

    def __post_init__(self) -> None:
        if self.width < 4 or self.height < 4:
            raise ValueError("terrain dimensions must be at least 4x4")
        if not 0.0 < self.ocean_fraction < 1.0:
            raise ValueError("ocean_fraction must be between 0 and 1")
        if self.mountain_strength < 0 or self.island_strength < 0:
            raise ValueError("terrain strengths cannot be negative")


@dataclass(frozen=True, slots=True)
class TerrainCell:
    x: int
    y: int
    elevation_m: float
    land: bool
    slope: float


class TerrainGenerator:
    """Deterministic multi-octave terrain generator for a bounded spherical-like grid."""

    def __init__(self, params: TerrainParams = TerrainParams()) -> None:
        self.params = params

    def _noise(self, x: float, y: float, octave: int, rng: random.Random) -> float:
        # Hash-like deterministic interpolation without third-party dependencies.
        seed = self.params.seed + octave * 1_000_003
        local = random.Random(seed)
        gx = math.floor(x)
        gy = math.floor(y)
        tx = x - gx
        ty = y - gy
        values: dict[tuple[int, int], float] = {}
        for ix in (gx, gx + 1):
            for iy in (gy, gy + 1):
                h = random.Random(local.randrange(0, 2**31) ^ (ix * 73856093) ^ (iy * 19349663))
                values[ix, iy] = h.random() * 2.0 - 1.0
        sx = tx * tx * (3.0 - 2.0 * tx)
        sy = ty * ty * (3.0 - 2.0 * ty)
        a = values[gx, gy] * (1.0 - sx) + values[gx + 1, gy] * sx
        b = values[gx, gy + 1] * (1.0 - sx) + values[gx + 1, gy + 1] * sx
        return a * (1.0 - sy) + b * sy

    def generate(self) -> tuple[tuple[TerrainCell, ...], ...]:
        p = self.params
        rng = random.Random(p.seed)
        raw: list[list[float]] = [[0.0] * p.width for _ in range(p.height)]
        for y in range(p.height):
            for x in range(p.width):
                nx = x / max(1, p.width - 1) * 6.0
                ny = y / max(1, p.height - 1) * 6.0
                value = 0.0
                amplitude = 1.0
                total = 0.0
                for octave in range(5):
                    value += amplitude * self._noise(nx * 2**octave, ny * 2**octave, octave, rng)
                    total += amplitude
                    amplitude *= 0.5
                value /= total
                # Low-frequency spherical mask produces broad continents and ocean basins.
                dx = abs(x / (p.width - 1) * 2.0 - 1.0)
                dy = abs(y / (p.height - 1) * 2.0 - 1.0)
                basin_bias = 0.18 * (dx**2 + dy**2)
                value += p.mountain_strength * value**3 - basin_bias
                # Occasional elevated interior/island structures.
                island = max(0.0, 1.0 - ((dx - 0.35) ** 2 + (dy + 0.15) ** 2) / 0.18)
                value += p.island_strength * island * island
                raw[y][x] = value

        flat = sorted(v for row in raw for v in row)
        cutoff = flat[max(0, min(len(flat) - 1, int(len(flat) * p.ocean_fraction)))]
        scale = max(1e-9, max(abs(v) for v in flat))
        result: list[list[TerrainCell]] = []
        for y in range(p.height):
            row: list[TerrainCell] = []
            for x in range(p.width):
                value = raw[y][x]
                land = value >= cutoff
                elevation = ((value - cutoff) / scale * 4200.0) if land else -((cutoff - value) / scale * 5200.0)
                neighbors = []
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if 0 <= nx < p.width and 0 <= ny < p.height:
                        neighbors.append(abs(raw[ny][nx] - value))
                slope = sum(neighbors) / max(1, len(neighbors))
                row.append(TerrainCell(x, y, elevation, land, slope))
            result.append(row)
        return tuple(tuple(row) for row in result)
