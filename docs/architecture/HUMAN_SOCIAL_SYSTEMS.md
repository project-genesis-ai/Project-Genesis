# Human Biology and Social Systems

Genesis models human physiology, social relationships, institutional memory, and generational learning as deterministic domain systems independent of rendering and external AI services.

## Human physiology

`HumanPhysiology` tracks life stage, nutrition, hydration, energy, sleep, injury, health, aging, recovery, and death. Parameters are replaceable and deliberately separated from the agent identity so richer biological models can be introduced without rewriting cognition.

## Social graph

`RelationshipGraph` stores directed relationships with trust, affinity, and interaction history. Family ties, friendship, rivalry, and household/group membership are explicit domain data rather than emergent strings.

## Social runtime

`SocialRuntime` is the authoritative per-tick bridge from agent personality and immediate need stress into deterministic pairwise social interaction. It updates trust and affinity, materializes rival relationships when persistent negative interaction crosses a bounded threshold, and derives friendship groups from positive affinity. Agent iteration is sorted by stable `agent_id`, so identical state produces identical social transitions.

The runtime is invoked by `Simulation.step()` after individual cognition/actions. It does not create a second decision authority and does not require an LLM, network, database, or wall-clock state.

## Cultural transmission

`CultureRuntime` executes after social dynamics and transfers previously learned agent knowledge only across sufficiently trusted friendship relationships. Transmission is deterministic, bounded to one new item per direction per pair per tick, and records the learning event in the recipient's episodic memory. Knowledge adopted by at least two living agents becomes an explicit shared tradition, providing a foundation for generational cultural continuity without requiring external AI.

## Institutional and generational knowledge

`KnowledgeRepository` separates institutional memory by domain. Trading knowledge stays in the trading domain, education knowledge in education, medicine in medicine, and so on. Experiences are immutable evidence records; lessons remain provisional until repeated evidence from independent actors reaches the configured verification threshold. Disputed lessons are never taught by the generational runtime.

`KnowledgeRuntime` is the authoritative bridge from verified institutional knowledge to living people. Each simulation tick it deterministically teaches a bounded number of verified lessons to each living agent and records transfers. A newborn therefore starts with a new biological memory but can immediately enter the same civilization-wide verified knowledge pipeline as every other citizen. The system does not copy a parent's private memory into a child's mind and does not treat unverified experience as truth.

The repository intentionally stores knowledge, not private conversations. A future external AI integration can use the domain repositories as an authorized educational context while preserving a separate boundary for private agent memory and consent-controlled research datasets.

## Social groups

Households and groups maintain membership, resources, cohesion, and reputation. Group membership is reconciled against living agents each tick so dead or removed agents do not remain as active members.

## Memory safety

Agent episodic memory is bounded by `MemoryStore.capacity` (256 by default). Duplicate memory IDs are ignored and low-value entries are deterministically evicted when capacity is exceeded. Collective historical memory is also bounded by `CulturalMemory.capacity` (2048 by default). Institutional experiences and lessons are independently bounded per domain. These bounds prevent long-running social/cognition simulation from accumulating unbounded memory.

## Determinism

No network or LLM dependency is required. Simulation time remains authoritative and all state transitions are bounded and validated. Knowledge verification is deterministic, domain-isolated, and reproducible from the recorded evidence IDs.
