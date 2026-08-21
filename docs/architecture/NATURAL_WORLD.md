# Natural World Foundation

## Physics

The first physics layer uses SI units and deterministic Newtonian mechanics. `PhysicsWorld` computes pairwise gravitational acceleration from immutable position snapshots and integrates bodies after all accelerations are computed. This keeps updates order-independent for a tick.

## Environment

`EnvironmentCell` stores biome, elevation, temperature, rainfall, water, and normalized vegetation. These values are authoritative simulation state and are intentionally independent of rendering.

## Living systems

Species define trophic role and ecological traits. Organisms hold mutable lifecycle state. Ecosystems track populations and expose predator-prey relationships. Forest dynamics couple vegetation growth to water availability and temperature.

## Reuse

Genesis will integrate mature scientific/agent-based libraries behind adapters when they improve correctness or scale. Existing research implementations remain references unless their code and licenses are explicitly suitable for reuse.
