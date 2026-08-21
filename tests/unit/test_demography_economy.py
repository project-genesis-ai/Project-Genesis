from genesis.demography import AgeStage, BirthRecord, DemographicSystem, HumanLifeState
from genesis.economy import Inventory, Job, LaborMarket, Trade, Wallet


def test_human_lifecycle_and_birth() -> None:
    system = DemographicSystem()
    person = HumanLifeState("a1", age_ticks=30)
    system.register(person)
    system.record_birth(BirthRecord("b1", ("a1",), "a2", 1))
    assert system.people["a2"].stage is AgeStage.INFANT
    person.age_ticks = 360
    assert system.step(0) == ("a1",)


def test_labor_market_wage_and_wallet_sync() -> None:
    market = LaborMarket()
    market.post(Job("j1", "Farmer", "farm", 3.5))
    assert market.hire("a1", "j1")
    assert market.wage("a1", 4) == 14.0
    wallet = Wallet("a1", 1)
    wallet.credit(market.wage("a1", 4))
    assert wallet.balance == 15.0


def test_trade_rolls_back_without_funds() -> None:
    buyer = Inventory()
    seller = Inventory()
    seller.add("grain", 2)
    buyer_wallet = Wallet("buyer", 1)
    seller_wallet = Wallet("seller", 0)
    trade = Trade("buyer", "seller", "grain", 2, 2)
    assert not trade.execute_with_money(buyer, seller, buyer_wallet, seller_wallet)
    assert seller.quantity("grain") == 2
    assert buyer.quantity("grain") == 0


def test_trade_moves_inventory_and_money() -> None:
    buyer = Inventory()
    seller = Inventory()
    seller.add("grain", 2)
    buyer_wallet = Wallet("buyer", 4)
    seller_wallet = Wallet("seller", 0)
    trade = Trade("buyer", "seller", "grain", 2, 2)
    assert trade.execute_with_money(buyer, seller, buyer_wallet, seller_wallet)
    assert buyer.quantity("grain") == 2
    assert seller.quantity("grain") == 0
    assert buyer_wallet.balance == 0
    assert seller_wallet.balance == 4
