"""ExecutionAgent integration tests."""

from datetime import datetime, timedelta, timezone

from src.agents.execution_agent import ExecutionAgent
from src.models.signals import RiskDecisionType
from src.models.trade import TradeState


def test_execute_happy_path_opens_trade(valid_proposal, valid_risk_decision):
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
    assert trade.fill_price > valid_proposal.entry_price
    assert trade.fill_price > 0
    assert trade.shares == valid_proposal.position_size_shares
    assert fill.trade_id == trade.trade_id


def test_execute_returns_block_reason_for_expired_decision(valid_proposal, valid_risk_decision):
    agent = ExecutionAgent()
    valid_risk_decision.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)

    trade, fill, error = agent.execute(
        proposal=valid_proposal,
        risk_decision=valid_risk_decision,
        current_price=valid_proposal.entry_price,
    )

    assert trade is None
    assert fill is None
    assert error is not None
    assert "expired" in error.lower()


def test_execute_returns_block_reason_for_hash_mismatch(valid_proposal, valid_risk_decision):
    agent = ExecutionAgent()
    valid_risk_decision.proposal_hash = "mismatched_hash"

    trade, fill, error = agent.execute(
        proposal=valid_proposal,
        risk_decision=valid_risk_decision,
        current_price=valid_proposal.entry_price,
    )

    assert trade is None
    assert fill is None
    assert error is not None
    assert "hash mismatch" in error.lower()


def test_execute_applies_reduce_size_condition(valid_proposal, valid_risk_decision):
    agent = ExecutionAgent()
    valid_risk_decision.conditions = ["reduce_size_by_50pct"]
    valid_risk_decision.decision_type = RiskDecisionType.APPROVED_WITH_CONDITIONS

    trade, fill, error = agent.execute(
        proposal=valid_proposal,
        risk_decision=valid_risk_decision,
        current_price=valid_proposal.entry_price,
    )

    assert error is None
    assert trade is not None
    assert fill is not None
    assert trade.shares == valid_proposal.position_size_shares // 2


def test_execute_still_runs_for_zero_current_price(valid_proposal, valid_risk_decision):
    agent = ExecutionAgent()

    trade, fill, error = agent.execute(
        proposal=valid_proposal,
        risk_decision=valid_risk_decision,
        current_price=0.0,
    )

    assert error is None
    assert trade is not None
    assert fill is not None
    assert trade.state == TradeState.OPEN


def test_execute_clamps_minimum_shares_after_reduction(valid_proposal, valid_risk_decision):
    agent = ExecutionAgent()
    valid_proposal.position_size_shares = 1
    valid_proposal.position_value_usd = valid_proposal.entry_price
    valid_proposal.max_loss_usd = abs(valid_proposal.entry_price - valid_proposal.stop_loss)
    valid_proposal.max_loss_pct = valid_proposal.max_loss_usd / valid_proposal.position_value_usd
    valid_proposal.proposal_hash = valid_proposal.compute_hash()

    valid_risk_decision.proposal_hash = valid_proposal.proposal_hash
    valid_risk_decision.conditions = ["reduce_size_by_50pct"]
    valid_risk_decision.decision_type = RiskDecisionType.APPROVED_WITH_CONDITIONS

    trade, fill, error = agent.execute(
        proposal=valid_proposal,
        risk_decision=valid_risk_decision,
        current_price=valid_proposal.entry_price,
    )

    assert error is None
    assert trade is not None
    assert fill is not None
    assert trade.shares == 1


def test_execute_with_none_risk_decision_returns_block_reason(valid_proposal):
    """risk_decision=None must be caught by gate.validate(), not reach _apply_conditions."""
    agent = ExecutionAgent()

    trade, fill, error = agent.execute(
        proposal=valid_proposal,
        risk_decision=None,
        current_price=valid_proposal.entry_price,
    )

    assert trade is None
    assert fill is None
    assert error is not None
