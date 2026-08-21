from genesis.biology.universal import (
    BiologicalIndividual,
    BiologicalTraits,
    EnvironmentExposure,
    Genome,
    IndividualIdentity,
    Population,
    SpeciesDefinition,
    EcologicalInteraction,
    environmentally_adapted_traits,
    ecological_pressure,
)


def make_individual(seed: int = 1, species: str = "wolf") -> BiologicalIndividual:
    genome = Genome.founder(seed)
    identity = IndividualIdentity.create(species, 0, genome, f"birth-{seed}")
    return BiologicalIndividual(identity, genome, BiologicalTraits(learning=0.8, sociality=0.7))


def test_identity_is_unique_even_when_genome_is_same():
    genome = Genome.founder(42)
    a = IndividualIdentity.create("human", 10, genome, "birth", 0)
    b = IndividualIdentity.create("human", 10, genome, "birth", 1)
    assert a.genome_fingerprint == b.genome_fingerprint
    assert a.identity_id != b.identity_id


def test_identity_rejects_ambiguous_birth_metadata():
    genome = Genome.founder(42)
    try:
        IndividualIdentity.create("human", 10, genome, "", 0)
        assert False, "empty birth event should fail"
    except ValueError as exc:
        assert "birth_event" in str(exc)


def test_reproduction_is_deterministic_and_mutation_is_lineage_based():
    a = Genome.founder(1)
    b = Genome.founder(2)
    first = a.reproduce(b, seed=99, mutation_rate=0.2)
    second = a.reproduce(b, seed=99, mutation_rate=0.2)
    assert first == second
    assert first.generation == 1
    assert first.fingerprint != a.fingerprint


def test_environment_changes_behavior():
    thirsty = make_individual()
    thirsty.internal.hydration = 0.2
    hungry = make_individual(2)
    hungry.internal.energy = 0.2
    assert thirsty.choose_action(EnvironmentExposure({"food": 0.8, "water": 0.1})) == "seek_water"
    assert hungry.choose_action(EnvironmentExposure({"food": 0.1, "water": 0.9})) == "seek_food"


def test_environment_changes_adaptive_phenotype_without_mutating_genome():
    genome = Genome.founder(7)
    identity = IndividualIdentity.create("wolf", 0, genome, "birth-7")
    base = BiologicalTraits()
    harsh = EnvironmentExposure({"food": 0.1, "water": 0.1, "danger": 0.9, "temperature": 0.0})
    adapted = environmentally_adapted_traits(base, harsh, adaptation_rate=1.0)
    assert adapted.resilience > base.resilience
    assert adapted.sensing > base.sensing
    assert adapted.mobility > base.mobility
    assert adapted.learning > base.learning
    assert genome.fingerprint == identity.genome_fingerprint


def test_danger_changes_behavior_and_internal_state_is_clamped():
    individual = make_individual()
    assert individual.choose_action(EnvironmentExposure({"food": 0.8, "water": 0.8, "danger": 1.0})) == "seek_shelter"
    assert 0.0 <= individual.internal.stress <= 1.0
    assert 0.0 <= individual.internal.safety <= 1.0


def test_population_rejects_duplicate_identity_and_wrong_species():
    population = Population("wolf", carrying_capacity=2)
    population.add(make_individual(1, "wolf"))
    try:
        population.add(make_individual(1, "wolf"))
        assert False, "duplicate identity should fail"
    except ValueError as exc:
        assert "duplicate" in str(exc)
    try:
        population.add(make_individual(2, "fox"))
        assert False, "wrong species should fail"
    except ValueError as exc:
        assert "species" in str(exc)


def test_species_definition_validates_rates():
    definition = SpeciesDefinition("oak", "plant", BiologicalTraits(), 0.4, 0.01, habitat=("forest",))
    assert definition.species_id == "oak"
    try:
        SpeciesDefinition("bad", "animal", BiologicalTraits(), 1.2, 0.01)
        assert False, "invalid reproduction rate should fail"
    except ValueError:
        pass


def test_ecological_pressure_is_deterministic_and_bidirectional():
    edges = (
        EcologicalInteraction("grass", "deer", "herbivory", 0.1),
        EcologicalInteraction("wolf", "deer", "predation", 0.2),
    )
    pressure = ecological_pressure(edges, {"grass": 100, "deer": 20, "wolf": 5})
    assert pressure["deer"] == 10.0 - 1.0
    assert pressure["wolf"] == -4.0
