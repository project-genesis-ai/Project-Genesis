from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from genesis.economy.wallet import Wallet


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True, slots=True)
class Asset:
    asset_id: str
    symbol: str
    price: float
    liquidity: float = 1.0

    def __post_init__(self) -> None:
        if not self.asset_id.strip() or not self.symbol.strip() or self.price < 0.0 or self.liquidity <= 0.0:
            raise ValueError("invalid asset")


@dataclass(frozen=True, slots=True)
class Order:
    order_id: str
    trader_id: str
    asset_id: str
    side: OrderSide
    quantity: float
    limit_price: float | None = None

    def __post_init__(self) -> None:
        if not self.order_id.strip() or not self.trader_id.strip() or not self.asset_id.strip() or self.quantity <= 0.0:
            raise ValueError("invalid order")
        if self.limit_price is not None and self.limit_price < 0.0:
            raise ValueError("invalid limit price")


@dataclass(frozen=True, slots=True)
class Trade:
    order_id: str
    trader_id: str
    asset_id: str
    side: OrderSide
    quantity: float
    price: float
    tick: int


@dataclass(slots=True)
class Portfolio:
    cash: Wallet
    positions: dict[str, float] = field(default_factory=dict)
    realized_pnl: float = 0.0

    def position(self, asset_id: str) -> float:
        return self.positions.get(asset_id, 0.0)

    def mark_to_market(self, assets: dict[str, Asset]) -> float:
        return self.cash.balance + sum(qty * assets[asset_id].price for asset_id, qty in self.positions.items() if asset_id in assets)


@dataclass(slots=True)
class Exchange:
    assets: dict[str, Asset] = field(default_factory=dict)
    portfolios: dict[str, Portfolio] = field(default_factory=dict)
    trades: list[Trade] = field(default_factory=list)
    max_trades: int = 100_000

    def add_asset(self, asset: Asset) -> None:
        if asset.asset_id in self.assets:
            raise ValueError(f"asset already exists: {asset.asset_id}")
        self.assets[asset.asset_id] = asset

    def register_trader(self, trader_id: str, wallet: Wallet) -> None:
        if trader_id in self.portfolios:
            return
        self.portfolios[trader_id] = Portfolio(wallet)

    def submit(self, order: Order, tick: int) -> Trade | None:
        if tick < 0 or order.asset_id not in self.assets or order.trader_id not in self.portfolios:
            return None
        asset = self.assets[order.asset_id]
        price = asset.price
        if order.limit_price is not None:
            if order.side is OrderSide.BUY and price > order.limit_price:
                return None
            if order.side is OrderSide.SELL and price < order.limit_price:
                return None
        portfolio = self.portfolios[order.trader_id]
        notional = price * order.quantity
        if order.side is OrderSide.BUY:
            if not portfolio.cash.debit(notional):
                return None
            portfolio.positions[order.asset_id] = portfolio.position(order.asset_id) + order.quantity
        else:
            if portfolio.position(order.asset_id) < order.quantity:
                return None
            portfolio.positions[order.asset_id] -= order.quantity
            portfolio.cash.credit(notional)
        trade = Trade(order.order_id, order.trader_id, order.asset_id, order.side, order.quantity, price, tick)
        self.trades.append(trade)
        if len(self.trades) > self.max_trades:
            del self.trades[: len(self.trades) - self.max_trades]
        return trade

    def set_price(self, asset_id: str, price: float) -> None:
        if asset_id not in self.assets or price < 0.0:
            raise ValueError("invalid price update")
        old = self.assets[asset_id]
        self.assets[asset_id] = Asset(old.asset_id, old.symbol, price, old.liquidity)
