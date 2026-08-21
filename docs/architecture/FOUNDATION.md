# Genesis Foundation Architecture

## Authority

The Python simulation engine is the authoritative source of world state. Visualization clients never own simulation truth.

## Core flow

`World + Time + Agent State -> Decision/Action -> Consequence -> Event -> State Update`

The current foundation establishes the state, clock, agent, validated-action boundary, and append-only event history needed for that flow.

## Determinism

Simulation time advances in discrete ticks. Configuration contains a simulation seed and tick step. Future stochastic systems must derive randomness from the simulation-owned deterministic source rather than ambient global randomness.

## Events

Important state changes are represented as immutable events. Events are ordered by simulation tick and form the basis for debugging, replay, and historical inspection.

## Agent boundary

Agents are data owned by the simulation. They do not execute arbitrary code. Actions must pass through an explicit validation boundary before they can mutate authoritative state.

## Expansion rule

New domains such as physics, ecosystems, animals, economy, society, and civilization will be added behind explicit domain interfaces. Existing open-source scientific/research implementations may be integrated where their license, validity, performance, and architecture fit Genesis.

## Testing rule

Every invariant introduced by the foundation has a unit or integration test. CI is intentionally run at batch/phase boundaries rather than for every small change.
