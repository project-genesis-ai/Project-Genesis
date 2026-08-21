import pytest
from genesis.economy import DoubleEntryLedger, Money
from genesis.physics import Energy, EnergyConversion, Power

def test_power_integrates_to_energy():
    assert Power(100.0).energy(60.0).joules == pytest.approx(6000.0)

def test_energy_conversion_conserves_bounded_fraction():
    assert EnergyConversion(0.4).convert(Energy(1000.0)).joules == pytest.approx(400.0)

def test_double_entry_ledger_balances():
    ledger = DoubleEntryLedger()
    ledger.post("buyer", "seller", Money(1250), "food")
    assert ledger.is_balanced()
    assert ledger.balance("buyer").minor_units == 1250
    assert ledger.balance("seller").minor_units == -1250

def test_money_rejects_currency_mismatch():
    with pytest.raises(ValueError):
        _ = Money(1, "A") + Money(1, "B")
