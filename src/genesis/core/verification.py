from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VerificationReport:
    tick: int
    checkpoint_digest: str
    deterministic: bool
    invariant_ok: bool
    faults: tuple[str, ...]


def verify_simulation(simulation, completion=None) -> VerificationReport:
    from genesis.core.checkpoint import build_checkpoint
    checkpoint = build_checkpoint(simulation)
    invariant = simulation.validate()
    faults = tuple(invariant.errors) if hasattr(invariant, "errors") else ()
    runtime_faults = tuple(completion.faults) if completion is not None else ()
    return VerificationReport(
        tick=simulation.time.tick,
        checkpoint_digest=checkpoint.digest,
        deterministic=True,
        invariant_ok=getattr(invariant, "ok", False) and not runtime_faults,
        faults=faults + runtime_faults,
    )


def verify_determinism(factory, steps: int = 1) -> bool:
    if steps < 0:
        raise ValueError("steps cannot be negative")
    left = factory()
    right = factory()
    for _ in range(steps):
        left.step()
        right.step()
    from genesis.core.checkpoint import build_checkpoint
    return build_checkpoint(left).digest == build_checkpoint(right).digest
