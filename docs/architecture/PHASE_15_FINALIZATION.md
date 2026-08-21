# Phase 15 — Finalization & Scientific Validation

## Purpose

Phase 15 is the final engineering acceptance layer. It does not invent another simulation subsystem. It proves that the existing authoritative domains can execute together for a meaningful bounded horizon while preserving deterministic replay and production invariants.

## Acceptance contract

A final validation run must prove:

1. repeated ticks complete without invariant violations;
2. hardening remains clean after every tick;
3. canonical checkpoint serialization remains stable;
4. two independently constructed simulations with the same seed remain identical after the full horizon;
5. final metrics remain finite;
6. population and wealth remain auditable;
7. no external service is required for the deterministic core.

The CI acceptance horizon is 100 simulation steps. Unit tests use a shorter horizon for fast regression coverage.

## Scope of validation

The probe exercises the already merged planet, water/climate, ecology, species/evolution, human cognition/social behavior, demography, civilization, economy/governance, knowledge/technology, autonomous orchestration, scaling, verification, hardening and cross-domain emergence layers through the canonical `Simulation` and `GenesisRuntime` authorities.

## Important boundary

Passing Phase 15 means the software system is internally consistent, deterministic and long-run executable under the acceptance scenario. It does **not** claim that every biological, climatic or socioeconomic parameter is scientifically calibrated to Earth. Calibration is an empirical research activity and must be represented by measured scenarios rather than an arbitrary completion percentage.
