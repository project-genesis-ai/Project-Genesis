# Geography and Climate System

Genesis geography is sparse and deterministic. A `GeoCell` describes elevation, latitude, biome, soil fertility, and water without forcing the world into a dense global grid.

`ClimateEngine` derives local temperature, humidity, precipitation, and wind from latitude, elevation, moisture, and authoritative simulation tick. It is deliberately replaceable so higher-fidelity climate models can be introduced without changing agent or ecosystem APIs.

`ResourceStock` models bounded resources with explicit harvesting and regeneration. This keeps depletion and renewal observable and deterministic.

The layer is independent of rendering and external services. Later world generation can populate continents, oceans, rivers, mountains, forests, and other terrain using these primitives.
