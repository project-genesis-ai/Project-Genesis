# Civilization Layer

The current layer introduces the first reusable abstractions above the natural world without pretending that a civilization already exists.

## Agent cognition

Agents now have memory, knowledge, skills, wealth, and an extensible need model. `DecisionEngine` is deterministic and rule-based. An LLM may later provide candidate reasoning through an adapter, but it cannot bypass action validation or become authoritative simulation state.

## Society

Relationships and social groups are explicit state. Relationships are canonicalized so A-B and B-A address the same relationship.

## Economy

Inventory, trades, and a small supply/demand market primitive establish a foundation for later production, jobs, money, businesses, and banking. Monetary balances remain explicit agent/government state rather than hidden side effects.

## Civilization

Institutions, governments, and technology are intentionally minimal primitives. They are not a hard-coded civilization. Future rules can allow these structures to emerge from population, resources, relationships, and events.

## Next integration boundary

The next major layer should connect these primitives to validated actions, agent perception, lifecycle, settlements, production, and multi-agent interaction. The simulation engine remains authoritative; visualization and external AI are consumers/adapters.
