# Physical resource state

Genesis keeps physical inventories separate from monetary accounting. `ResourceStock` stores non-negative material quantities, while `Money` and the double-entry ledger represent their monetary counterpart. Utility networks track settlement water in cubic metres and electricity in joules/kWh.

`SimulationState` owns these systems as authoritative state so future agriculture, industry, settlement, trade and agent consumption can operate on the same physical pools rather than duplicated counters.
