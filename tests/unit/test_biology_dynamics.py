from genesis.biology.dynamics import BiologicalDynamics, InfectionState, population_snapshot
from genesis.biology.universal import BiologicalTraits, EnvironmentExposure, Genome, IndividualIdentity, BiologicalIndividual, Population


def individual(species: str, seed: int, tick: int = 0) -> BiologicalIndividual:
    genome = Genome.founder(seed)
    return BiologicalIndividual(IndividualIdentity.create(species, tick, genome, f"birth-{seed}"), genome, BiologicalTraits(learning=0.8))


def test_reproduction_preserves_species_and_creates_new_identity():
    a = individual("bird", 1)
    b = individual("bird", 2)
    child = BiologicalDynamics.reproduce(a, b, seed=4, birth_tick=12, species_id="bird", birth_event="pair-1", mutation_rate=0.01)
    assert child.identity.species_id == "bird"
    assert child.identity.identity_id not in {a.identity.identity_id, b.identity.identity_id}
    assert child.genome.generation == 1


def test_migration_is_deterministic_and_prefers_highest_pressure_then_id():
    a = individual("bird", 1)
    result = BiologicalDynamics.migrate(a, "north", (("south", 0.5), ("east", 0.9), ("west", 0.9)))
    assert result is not None
    assert result.destination == "east"


def test_transmission_is_deterministic_and_application_changes_state():
    host = individual("mammal", 1)
    infection = InfectionState("flu", host.identity.identity_id, load=0.8, transmissibility=1.0, damage=0.2)
    before = host.internal.energy
    BiologicalDynamics.apply_infection(host, infection)
    assert host.internal.energy < before
    a = BiologicalDynamics.transmit(infection, ["h2", "h1"], seed=5)
    b = BiologicalDynamics.transmit(infection, ["h2", "h1"], seed=5)
    assert a == b
    assert {x.host_id for x in a} == {"h1", "h2"}


def test_population_snapshot_is_stable():
    population = Population("plant")
    population.add(individual("plant", 1))
    population.add(individual("plant", 2))
    snapshot = population_snapshot(population)
    assert snapshot["species_id"] == "plant"
    assert snapshot["size"] == 2
    assert snapshot["identities"] == sorted(snapshot["identities"])
