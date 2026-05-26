"""Tests for ExecutionAgent risk-condition handling."""

from src.agents.execution_agent import ExecutionAgent
from src.models.signals import RiskDecisionType


def test_reduce_size_condition_parses_requested_percentage(valid_proposal, valid_risk_decision):
    agent = ExecutionAgent()
    valid_risk_decision.conditions = ["reduce_size_by_50pct"]
    valid_risk_decision.decision_type = RiskDecisionType.APPROVED_WITH_CONDITIONS

    adjusted = agent._apply_conditions(valid_proposal, valid_risk_decision)

    assert adjusted.position_size_shares == valid_proposal.position_size_shares // 2


def test_reduce_size_condition_clamps_to_minimum_share(valid_proposal, valid_risk_decision):
    agent = ExecutionAgent()
    valid_proposal.position_size_shares = 1
    valid_proposal.position_value_usd = valid_proposal.entry_price
    valid_proposal.max_loss_usd = abs(valid_proposal.entry_price - valid_proposal.stop_loss)
    valid_proposal.max_loss_pct = valid_proposal.max_loss_usd / valid_proposal.position_value_usd
    valid_proposal.proposal_hash = valid_proposal.compute_hash()

    valid_risk_decision.proposal_hash = valid_proposal.proposal_hash
    valid_risk_decision.conditions = ["reduce_size_by_50pct"]
    valid_risk_decision.decision_type = RiskDecisionType.APPROVED_WITH_CONDITIONS

    adjusted = agent._apply_conditions(valid_proposal, valid_risk_decision)

    assert adjusted.position_size_shares == 1


def test_unparseable_reduce_size_condition_defaults_to_twenty_percent(valid_proposal, valid_risk_decision):
    agent = ExecutionAgent()
    valid_risk_decision.conditions = ["reduce_size"]
    valid_risk_decision.decision_type = RiskDecisionType.APPROVED_WITH_CONDITIONS

    adjusted = agent._apply_conditions(valid_proposal, valid_risk_decision)

    assert adjusted.position_size_shares == int(valid_proposal.position_size_shares * 0.8)
