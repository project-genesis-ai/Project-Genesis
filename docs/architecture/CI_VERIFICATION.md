# CI Verification Contract

The deterministic core must be merge-gated by the complete CI suite. Tests that compare floating-point derived metrics must use tolerance-aware assertions, while event assertions must target the public `SimulationEvent.event_type` field. These rules prevent test failures caused by representation details or stale assumptions about the event API.

The current root-cause gate also covers deterministic canonicalization of stateful runtime objects and cross-domain runtime invariants.
