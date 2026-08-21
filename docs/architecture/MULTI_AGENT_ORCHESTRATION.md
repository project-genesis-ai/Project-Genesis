# Multi-Agent Engineering Orchestration

Project Genesis now has a dependency-free orchestration layer for coordinating a large specialist fleet without moving simulation authority into the agents.

## Design principles

1. **The deterministic simulation remains authoritative.** Agents coordinate engineering work; they do not mutate planetary or civilization state directly through this layer.
2. **Structured shared state replaces transcript sharing.** Findings, decisions, artifacts, failures, approvals, and node status are bounded and auditable.
3. **Routing is deterministic.** Agent capability scores use task keywords and stable tie-breaking by agent ID.
4. **Related work can fan out.** Specialist nodes depend on architecture and can execute in deterministic waves before integration.
5. **Integration is a gate.** Integrator and reviewer nodes are always downstream of specialists.
6. **Human approval is risk-based.** Normal tasks can ship after verification; deployment, migration, destructive, credential, permission, production, or irreversible work requires the explicit `high-impact` approval checkpoint.
7. **Provider-neutral execution.** An `AgentDefinition` accepts a handler. A handler may later wrap a local tool, coding agent, research model, or external provider without adding that dependency to the Genesis core.

## Standard fleet

The default registry covers repository audit, research, architecture, planetary science, climate, hydrology, ocean systems, ecology, animals, evolution, human systems, society/culture, civilization, economy/finance, politics/government, technology, transport, knowledge, backend/API, security, performance, QA, debugging, DevOps/CI, integration, review, human approval, and shipping.

The fleet is intentionally extensible. New domains are registered as capabilities rather than hard-coded into the scheduler.

## Workflow

```text
Research
   |
Architecture
   |
+---------------- specialist fan-out ----------------+
| planet | climate | water | life | humans | economy |
| politics | technology | transport | QA | security |
+-----------------------------------------------------+
   |
Integrator
   |
Reviewer
   |
   +---- normal task --------------------> Ship
   |
   +---- high-impact -> Human Checkpoint -> Ship
```

## Failure handling

Agent exceptions are contained at the adapter boundary and converted to structured failures. Retryable results can be retried up to the node's attempt limit. A failed dependency prevents downstream success-only nodes from running. The final result is `SUCCEEDED`, `FAILED`, or `BLOCKED` and includes executed, blocked, and failed node IDs.

## Scale and safety controls

- bounded shared findings/artifacts/failures;
- bounded workflow node count;
- bounded agents per execution wave;
- per-agent concurrency limits;
- duplicate agent registration rejection;
- workflow missing-dependency and cycle detection;
- stable routing and execution ordering;
- explicit approval set for high-impact checkpoints.

## External execution boundary

The orchestration layer deliberately does not embed an LLM SDK, Git client, database client, or network service. A production controller can adapt its existing tool integrations to `AgentDefinition.handler`, while the deterministic graph and state contracts remain testable in isolation.
