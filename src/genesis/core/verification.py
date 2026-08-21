from __future__ import annotations

from dataclasses import dataclass
import copy


@dataclass(frozen=True, slots=True)
class VerificationReport:
    tick: int
    checkpoint_digest: str
    deterministic: bool
    invariant_ok: bool
    faults: tuple[str, ...]


def verify_simulation(simulation, completion=None, *, determinism_steps: int = 1) -> VerificationReport:
    """Verify the current state and independently replay a cloned simulation.

    The live simulation is never mutated by the determinism probe. A checkpoint
    digest alone proves serialization stability; the twin-run comparison additionally
    proves that equal authoritative state produces equal future state.
    """
    if determinism_steps < 0:
        raise ValueError("determinism_steps cannot be negative")
    from genesis.core.checkpoint import build_checkpoint

    checkpoint = build_checkpoint(simulation)
    invariant = simulation.validate()
    faults = list(getattr(invariant, "errors", ()))
    runtime_faults = tuple(completion.faults) if completion is not None else ()
    faults.extend(runtime_faults)

    deterministic = True
    try:
        left = copy.deepcopy(simulation)
        right = copy.deepcopy(simulation)
        for _ in range(determinism_steps):
            left.step()
            right.step()
        deterministic = build_checkpoint(left).digest == build_checkpoint(right).digest
    except Exception as exc:
        deterministic = False
        faults.append(f"determinism probe failed: {type(exc).__name__}: {exc}")

    if not deterministic:
        faults.append("twin-run checkpoint mismatch")
    return VerificationReport(
        tick=simulation.time.tick,
        checkpoint_digest=checkpoint.digest,
        deterministic=deterministic,
        invariant_ok=getattr(invariant, "ok", False) and not runtime_faults and deterministic,
        faults=tuple(dict.fromkeys(faults)),
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
