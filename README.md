# Project Genesis

A research-driven, open-source simulation of a persistent world where physical processes, ecosystems, agents, societies, economies, and civilizations can emerge from explicit rules and interactions.

## Current status

Natural-world foundation batch: deterministic physics and living-system primitives are implemented on top of the verified simulation core.

## Current layers

- Deterministic simulation clock and state.
- Newtonian vector, gravity, body, and pairwise N-body physics primitives.
- Environment cells with biome, elevation, temperature, rainfall, water, and vegetation state.
- Species, trophic levels, individual organisms, forest vegetation dynamics, and ecosystem interactions.
- Research/reuse policy for integrating mature open-source simulation components.

The authoritative simulation remains Python-first. Visualization and external engines will consume simulation state rather than define it.

## Development principle

Genesis is developed in large verified batches. CI is intentionally minimized: complete a practical phase batch, run CI, fix root causes until green, review, then merge.
