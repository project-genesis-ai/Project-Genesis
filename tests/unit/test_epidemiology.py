import random

from genesis.health import Contact, Disease, Epidemiology

def test_high_hazard_seeded_contact_transmits():
    epi = Epidemiology(rng=random.Random(1))
    epi.register('a')
    epi.register('b')
    disease = Disease('flu', severity=0.2, transmission=1.0, duration_ticks=5)
    epi.states['a'].infect(disease)
    assert epi.expose(Contact('a', 'b', contacts_per_day=10.0), disease)
    assert 'flu' in epi.states['b'].diseases

def test_vaccination_blocks_transmission():
    epi = Epidemiology(rng=random.Random(1))
    epi.register('a')
    epi.register('b')
    disease = Disease('flu', severity=0.2, transmission=1.0, duration_ticks=5)
    epi.states['a'].infect(disease)
    epi.vaccinate('b', 'flu')
    assert not epi.expose(Contact('a', 'b', contacts_per_day=10.0), disease)

def test_zero_contact_cannot_transmit():
    disease = Disease('flu', severity=0.2, transmission=0.1, duration_ticks=5)
    epi = Epidemiology(rng=random.Random(4))
    epi.register('a')
    epi.register('b')
    epi.states['a'].infect(disease)
    assert not epi.expose(Contact('a', 'b', contacts_per_day=0.0), disease)
