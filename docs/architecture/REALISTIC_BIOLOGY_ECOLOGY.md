# Realistic biology and ecology

Genesis treats physical and biological quantities as explicit model quantities rather than arbitrary counters.

- Energy demand uses watts and joules with allometric mass scaling (`mass^0.75`).
- Organisms carry quantitative genomes whose traits are inherited with bounded stochastic mutation.
- Reproduction requires maturity and same-species pairing and is reduced by population density.
- Carrying capacity provides a simple density-dependent population ceiling.
- Randomness is injected through a seedable generator so experiments remain reproducible.

These equations are scientifically motivated approximations. They are not presented as a universal replacement for species-specific physiology. Species-specific coefficients and models can be added without changing the simulation contracts.
