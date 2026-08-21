# Civilization and Infrastructure

Genesis keeps civic, biological, cultural, disaster, and transport systems deterministic and independent from rendering, network services, and LLMs.

## Integrated domains

- Health: injury, disease duration, recovery, and immunity.
- Government: citizens, laws, treasury, services, and approval dynamics.
- Technology: prerequisite validation and progressive research.
- Culture: persistent historical events and traditions.
- Disasters: deterministic activation, duration, and historical completion events.
- Transport: weighted road graph with condition-aware travel time.

All systems are owned by `SimulationState` and advanced by the authoritative simulation clock. Domain objects validate their own invariants so invalid state cannot silently enter the simulation.
