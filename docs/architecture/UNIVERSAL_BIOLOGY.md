# Universal Biology

Genesis now has a domain-neutral biological layer shared by all living species.

## Authority boundary

`genesis.life.Ecosystem`, `Organism`, `Species`, planetary state, and existing evolution/health systems remain authoritative. `genesis.biology.bridge` is an adapter and must not maintain a second copy of runtime truth.

## Individual model

Each individual has an immutable simulation `identity_id` that is independent of its genome fingerprint. This permits genetically identical individuals (for example, twins) to remain distinct simulation entities.

The genome layer supports deterministic founder genomes, parent recombination, generation tracking, and mutation. Environmental exposure is represented separately from inherited genome so environment changes behavior and physiology without incorrectly mutating DNA directly.

## Universal causal loop

`genome + physiology + environment + internal state + memory -> behavior -> ecological/social effects -> changed environment -> future behavior`

Species can opt into different sensing, learning, sociality, cognition, mobility, fertility, and resilience levels. A plant, insect, bird, mammal, and human therefore share infrastructure without being forced into the same cognition model.

## Population and ecology

Population invariants prevent duplicate identities and species mismatches. Deterministic helpers cover reproduction, migration choice, host-pathogen transmission, infection impact, and food-web interaction pressure. Existing ecosystem reproduction, migration, food-web, and evolution systems remain the execution authority.

## Determinism

All generated identities, genomes, migration ranking, transmission sampling, and bridge projections use stable hashes or sorted iteration. Python's process-randomized `hash()` must never be used for simulation state.

## Scale

The model is individual-capable but supports population snapshots and bounded carrying capacity. This allows high-detail individuals where required while preserving an aggregate path for very large populations.
