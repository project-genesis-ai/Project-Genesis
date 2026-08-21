# Demography, Labor, and Money

This layer connects human lifecycle and economic activity without making the simulation dependent on an external database or service.

- Demography owns age stages, births, fertility, and deterministic old-age death.
- LaborMarket owns jobs, hiring, firing, and wage calculation.
- Wallet owns balances and atomic participant-to-participant transfers.
- Trade can settle both inventory and money with preflight checks, so failed trades do not mutate state.
- SimulationState owns these systems; Simulation advances them using the authoritative clock.

Agent wealth remains synchronized with the authoritative wallet balance. Agent age remains synchronized with demographic state.
