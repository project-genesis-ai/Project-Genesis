# World and Ecology Scale

Genesis keeps Python authoritative for the natural world. The current ecological layer is intentionally deterministic and composable rather than tied to rendering.

## Layers

- `ClimateModel` updates temperature, humidity, precipitation, and wind.
- `Environment` stores biome cells and their climate state.
- `HabitatMap` provides sparse spatial cells for local organism interactions.
- `EcologicalBehavior` handles local foraging and movement.
- `FoodWeb` transfers energy through explicit predator/prey relationships.
- `PopulationDynamics` handles maturity, reproduction, carrying capacity, and natural crowding mortality.
- `LifeSystem` coordinates climate, vegetation, organism lifecycle, trophic interactions, and births each simulation step.

## Determinism

Random decisions use explicit seeded generators. Simulation time is passed into life systems from the authoritative simulation clock. No external network or LLM dependency is required for these systems.

## Scaling direction

The spatial layer is sparse so the world can grow without allocating a dense global grid. Individual organisms can be simulated where detail matters; later population-level approximations can aggregate distant populations without changing the domain interfaces.

## Scientific boundary

These are computational models, not claims of exact planetary climate prediction. Parameters and equations remain replaceable so higher-fidelity scientific models can be integrated later without coupling them to agents or rendering.
