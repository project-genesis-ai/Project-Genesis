from __future__ import annotations

from dataclasses import dataclass, field

from genesis.finance.exchange import Exchange, Order, OrderSide


@dataclass(frozen=True, slots=True)
class TradingLesson:
    lesson_id: str
    domain: str
    title: str
    evidence_count: int = 1
    confidence: float = 0.0

    def __post_init__(self) -> None:
        if not self.lesson_id.strip() or not self.domain.strip() or not self.title.strip() or self.evidence_count < 1 or not 0.0 <= self.confidence <= 1.0:
            raise ValueError("invalid trading lesson")


@dataclass(slots=True)
class TraderProfile:
    trader_id: str
    skill: float = 0.0
    risk_score: float = 0.0
    trades: int = 0
    wins: int = 0
    losses: int = 0
    experience: list[str] = field(default_factory=list)
    max_experience: int = 2_000

    @property
    def win_rate(self) -> float:
        return self.wins / self.trades if self.trades else 0.0

    def record(self, trade_id: str, profitable: bool) -> None:
        if not trade_id.strip():
            raise ValueError("trade id cannot be empty")
        self.trades += 1
        self.wins += int(profitable)
        self.losses += int(not profitable)
        self.experience.append(trade_id)
        if len(self.experience) > self.max_experience:
            del self.experience[: len(self.experience) - self.max_experience]
        target = self.win_rate
        self.skill = min(1.0, max(self.skill, target))


@dataclass(slots=True)
class TradingAcademy:
    lessons: dict[str, TradingLesson] = field(default_factory=dict)
    enrollments: dict[str, set[str]] = field(default_factory=dict)

    def publish(self, lesson: TradingLesson) -> None:
        existing = self.lessons.get(lesson.lesson_id)
        if existing is not None:
            if lesson.evidence_count < existing.evidence_count:
                raise ValueError("lesson evidence cannot regress")
        self.lessons[lesson.lesson_id] = lesson

    def enroll(self, trader_id: str, lesson_id: str) -> None:
        if lesson_id not in self.lessons:
            raise ValueError(f"unknown lesson: {lesson_id}")
        self.enrollments.setdefault(trader_id, set()).add(lesson_id)

    def lessons_for(self, trader_id: str) -> tuple[TradingLesson, ...]:
        return tuple(self.lessons[key] for key in sorted(self.enrollments.get(trader_id, set())))


@dataclass(slots=True)
class TradingCompany:
    company_id: str
    exchange: Exchange = field(default_factory=Exchange)
    academy: TradingAcademy = field(default_factory=TradingAcademy)
    traders: dict[str, TraderProfile] = field(default_factory=dict)
    capital_limits: dict[str, float] = field(default_factory=dict)

    def hire(self, trader: TraderProfile, capital_limit: float = 0.0) -> None:
        if not self.company_id.strip() or not trader.trader_id.strip() or capital_limit < 0.0:
            raise ValueError("invalid trading company hire")
        self.traders[trader.trader_id] = trader
        self.capital_limits[trader.trader_id] = capital_limit

    def place(self, order: Order, tick: int) -> object | None:
        trader = self.traders.get(order.trader_id)
        if trader is None:
            return None
        asset = self.exchange.assets.get(order.asset_id)
        if asset is None:
            return None
        if order.side is OrderSide.BUY and asset.price * order.quantity > self.capital_limits.get(order.trader_id, 0.0):
            return None
        return self.exchange.submit(order, tick)
