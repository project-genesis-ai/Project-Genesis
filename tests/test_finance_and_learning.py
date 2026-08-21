from genesis.agents.agent import Agent
from genesis.core.state import SimulationState
from genesis.education.ai_assistant import LearningAssistant
from genesis.finance.exchange import Asset, Order, OrderSide
from genesis.finance.trading import TradingLesson
from genesis.knowledge.model import Experience, KnowledgeStatus


def test_exchange_enforces_cash_and_position_invariants() -> None:
    state = SimulationState()
    state.add_agent(Agent("trader", "Trader", wealth=1_000.0))
    state.register_trader("trader", capital_limit=1_000.0)
    state.trading_company.exchange.add_asset(Asset("a", "A", 100.0))

    buy = state.trading_company.place(Order("o1", "trader", "a", OrderSide.BUY, 5), 1)
    assert buy is not None
    assert state.wallets["trader"].balance == 500.0
    assert state.trading_company.exchange.portfolios["trader"].position("a") == 5.0

    sell = state.trading_company.place(Order("o2", "trader", "a", OrderSide.SELL, 5), 2)
    assert sell is not None
    assert state.wallets["trader"].balance == 1_000.0
    assert state.trading_company.exchange.portfolios["trader"].position("a") == 0.0


def test_trading_capital_limit_rejects_oversized_buy() -> None:
    state = SimulationState()
    state.add_agent(Agent("trader", "Trader", wealth=10_000.0))
    state.register_trader("trader", capital_limit=100.0)
    state.trading_company.exchange.add_asset(Asset("a", "A", 100.0))
    assert state.trading_company.place(Order("o", "trader", "a", OrderSide.BUY, 2), 1) is None


def test_verified_trading_knowledge_reaches_company_and_ai_context() -> None:
    state = SimulationState()
    for tick, actor in enumerate(("a", "b", "c")):
        state.record_knowledge_experience(
            Experience(f"e{tick}", "trading", actor, tick, "market", "hold", "stable", True, 0.8)
        )
    lesson = state.knowledge.propose_lesson(
        lesson_id="l1", domain="trading", statement="The tested setup survived the observed regime.", evidence_ids=("e0", "e1", "e2")
    )
    assert lesson.status is KnowledgeStatus.VERIFIED
    assert state.publish_verified_trading_knowledge() == ("l1",)
    assert state.trading_company.academy.lessons["l1"].confidence == 0.8
    message = state.learning_assistant.ask("a", "Explain this lesson.", ("trading",))
    assert message.lesson_ids == ("l1",)


def test_learning_assistant_history_is_bounded() -> None:
    assistant = LearningAssistant(max_history_per_learner=2)
    for index in range(4):
        assistant.ask("learner", f"q{index}")
    assert [m.prompt for m in assistant.history["learner"]] == ["q2", "q3"]


def test_trading_lesson_rejects_invalid_confidence() -> None:
    try:
        TradingLesson("x", "trading", "bad", 1, 2.0)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid confidence must be rejected")
