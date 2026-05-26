"""Tests for TradeStore persistence."""

from src.memory.trade_store import TradeStore
from src.models.trade import Direction, OrderType, Trade, TradeState


def test_upsert_trade_persists_partial_pnl(tmp_path):
    store = TradeStore(db_path=str(tmp_path / "trades.db"))
    trade = Trade(
        proposal_id="proposal-1",
        signal_id="signal-1",
        symbol="AAPL",
        direction=Direction.LONG,
        state=TradeState.CLOSED,
        order_type=OrderType.LIMIT,
        entry_price=150.0,
        fill_price=150.0,
        shares=5,
        gross_value=750.0,
        stop_loss=147.5,
        take_profit=155.0,
        max_loss_usd=12.5,
        risk_reward_ratio=2.0,
        partial_pnl=5.0,
        realized_pnl=15.0,
    )

    store.upsert_trade(trade)
    closed = store.get_closed_trades(limit=1)

    assert closed[0]["partial_pnl"] == 5.0
    assert closed[0]["realized_pnl"] == 15.0
