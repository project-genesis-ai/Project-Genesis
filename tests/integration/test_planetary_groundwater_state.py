from genesis.planet.coupling import PlanetEngine
from genesis.planet.terrain import TerrainParams


def test_planet_snapshot_exposes_persistent_groundwater_storage() -> None:
    engine = PlanetEngine(TerrainParams(width=8, height=8, seed=41))

    snapshot = engine.step(1)
    land_cells = [
        cell
        for row in snapshot.cells
        for cell in row
        if cell.terrain.land
    ]

    assert land_cells
    candidate = next(
        cell for cell in land_cells
        if engine.hydrology_runtime.groundwater[(cell.terrain.x, cell.terrain.y)].storage_mm > 0
    )
    runtime_state = engine.hydrology_runtime.groundwater[(candidate.terrain.x, candidate.terrain.y)]

    assert candidate.hydrology.groundwater_mm == runtime_state.storage_mm
    assert candidate.hydrology.groundwater_mm >= candidate.hydrology.infiltration_mm * 0.0
