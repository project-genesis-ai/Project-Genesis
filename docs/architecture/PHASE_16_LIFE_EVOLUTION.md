# Phase 16 — Life & Evolution

## Root cause

Genesis already had species, quantitative genomes, inheritance, environmental selection pressure, food webs and a universal biology adapter, but these concerns were not connected by one explicit, species-agnostic evolutionary accounting layer. Individual ancestry and relative fitness were therefore difficult to audit consistently.

## Contract

`EvolutionRuntime` is derived evolutionary state over the canonical `Organism`/`Ecosystem` authorities. It provides:

- stable genome records and ancestry;
- generation tracking;
- genome distance;
- bounded heritable-fitness evaluation;
- deterministic environmental selection probability;
- bounded audit history.

It deliberately does **not** kill organisms or create populations. Survival and reproduction remain authoritative in the existing life/population systems. This prevents a second biological authority and makes evolutionary evaluation safe to compose with future human and non-human species.

## Environment → evolution

`LifeSystem` computes food scarcity, predation, disease, temperature stress and water scarcity from the current environment/ecosystem. Those pressures are deterministically aggregated and passed to the universal evolutionary runtime.

The resulting fitness records are observable for validation and future speciation/calibration work without changing the existing ecological state transitions.

## Verification

Regression coverage verifies deterministic fitness, bounded probabilities, stable ancestry generation and non-zero genome distance. The existing full CI suite remains the acceptance gate.
