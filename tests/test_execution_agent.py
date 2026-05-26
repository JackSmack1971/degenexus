"""ExecutionAgent integration tests."""

from src.agents.execution_agent import ExecutionAgent
from src.models.trade import TradeState


def test_execute_opens_trade(valid_proposal, valid_risk_decision):
    agent = ExecutionAgent()

    trade, fill, error = agent.execute(
        proposal=valid_proposal,
        risk_decision=valid_risk_decision,
        current_price=valid_proposal.entry_price,
    )

    assert error is None
    assert trade is not None
    assert fill is not None
    assert trade.state == TradeState.OPEN
    assert trade.opened_at is not None
    assert trade.fill_price > 0
    assert trade.shares == valid_proposal.position_size_shares
    assert fill.trade_id == trade.trade_id
