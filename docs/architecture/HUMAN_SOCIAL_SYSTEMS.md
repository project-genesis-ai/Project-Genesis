# Human Biology and Social Systems

Genesis models human physiology and social relationships as deterministic domain systems independent of rendering and external AI services.

## Human physiology

`HumanPhysiology` tracks life stage, nutrition, hydration, energy, sleep, injury, health, aging, recovery, and death. Parameters are replaceable and deliberately separated from the agent identity so richer biological models can be introduced without rewriting cognition.

## Social graph

`RelationshipGraph` stores directed relationships with trust, affinity, and interaction history. Family ties, friendship, rivalry, and household/group membership are explicit domain data rather than emergent strings.

## Social runtime

`SocialRuntime` is the authoritative per-tick bridge from agent personality and immediate need stress into deterministic pairwise social interaction. It updates trust and affinity, materializes rival relationships when persistent negative interaction crosses a bounded threshold, and derives friendship groups from positive affinity. Agent iteration is sorted by stable `agent_id`, so identical state produces identical social transitions.

The runtime is invoked by `Simulation.step()` after individual cognition/actions. It does not create a second decision authority and does not require an LLM, network, database, or wall-clock state.

## Cultural transmission

`CultureRuntime` executes after social dynamics and transfers previously learned agent knowledge only across sufficiently trusted friendship relationships. Transmission is deterministic, bounded to one new item per direction per pair per tick, and records the learning event in the recipient's episodic memory. Knowledge adopted by at least two living agents becomes an explicit shared tradition, providing a foundation for generational cultural continuity without requiring external AI.

## Social groups

Households and groups maintain membership, resources, cohesion, and reputation. Group membership is reconciled against living agents each tick so dead or removed agents do not remain as active members.

## Memory safety

Agent episodic memory is bounded by `MemoryStore.capacity` (256 by default). Duplicate memory IDs are ignored and low-value entries are deterministically evicted when capacity is exceeded. Collective historical memory is also bounded by `CulturalMemory.capacity` (2048 by default). These bounds prevent long-running social/cognition simulation from accumulating unbounded memory.

## Determinism

No network or LLM dependency is required. Simulation time remains authoritative and all state transitions are bounded and validated.
