# Project Genesis

A research-driven, open-source simulation of a persistent world where physical processes, ecosystems, agents, societies, economies, and civilizations can emerge from explicit rules and interactions.

## Current status

Foundation batch in progress on `foundation/initial-architecture`.

The first foundation establishes:

- deterministic simulation time
- authoritative simulation state
- first citizen model
- needs and personality primitives
- validated action boundary
- immutable simulation events and ordered history
- initial unit/integration tests
- pull-request CI

## Architecture principle

Python owns simulation truth. Visualization is a separate client. Domain systems are added incrementally and may reuse mature open-source scientific or research implementations when they fit Genesis requirements and licensing.

## Development principle

Genesis is developed in large verified batches. CI is intentionally minimized: complete a practical phase batch, run CI, fix root causes until green, review, then merge.
