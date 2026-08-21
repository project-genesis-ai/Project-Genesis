from genesis.civilization.government import Government
from genesis.civilization.governance_runtime import GovernanceRuntime


def test_taxation_is_deterministic_and_conserves_money():
    runtime = GovernanceRuntime(tax_rate=0.10)
    runtime.add_government(Government("g", "Civic Union"))
    runtime.register_citizen("g", "b", balance=100.0)
    runtime.register_citizen("g", "a", balance=50.0)
    before = runtime.money_supply()

    collected = runtime.collect_taxes("g", {"a": 50.0, "b": 100.0})

    assert collected == 15.0
    assert runtime.governments["g"].treasury == 15.0
    assert runtime.wallets["a"].balance == 45.0
    assert runtime.wallets["b"].balance == 90.0
    assert runtime.reconcile(before)
    assert [event.subject_id for event in runtime.last_events] == ["a", "b"]


def test_service_spending_is_budget_bounded():
    runtime = GovernanceRuntime(service_budget_ratio=0.5)
    government = Government("g", "Civic Union", treasury=100.0)
    runtime.add_government(government)

    assert not runtime.fund_services("g", "health", 51.0)
    assert runtime.fund_services("g", "health", 50.0)
    assert government.treasury == 50.0
    assert government.public_services["health"] == 50.0


def test_transfer_preserves_total_private_money():
    runtime = GovernanceRuntime()
    runtime.ensure_wallet("a", 40.0)
    runtime.ensure_wallet("b", 10.0)
    before = runtime.money_supply()

    assert runtime.transfer("a", "b", 15.0)
    assert runtime.money_supply() == before
    assert runtime.wallets["a"].balance == 25.0
    assert runtime.wallets["b"].balance == 25.0


def test_government_tick_is_stable_for_same_state():
    left = Government("g", "Civic Union", treasury=100.0)
    right = Government("g", "Civic Union", treasury=100.0)
    for government in (left, right):
        government.add_citizen("a")
        government.spend("roads", 20.0)
        government.tick()
    assert left.approval == right.approval
