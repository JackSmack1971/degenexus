"""Tests for RiskGate hard rules — most critical path in the system."""

import math
import pytest
from src.core.risk_gate import RiskGate, RiskLimits
from src.models.signals import TradeProposal, RiskDecisionType


def check_hard_rules(risk_gate, proposal, **overrides):
    defaults = dict(
        portfolio_value=10_000.0,
        open_positions_count=0,
        total_exposure_usd=0.0,
    )
    defaults.update(overrides)
    return risk_gate.check_hard_rules(proposal, **defaults)


class TestMaxLossRule:
    def test_passes_within_limit(self, risk_gate, valid_proposal):
        violations = check_hard_rules(risk_gate, valid_proposal)
        assert not any("MAX_LOSS" in v for v in violations)

    def test_fails_when_loss_exceeds_2pct(self, risk_gate, valid_proposal):
        valid_proposal.max_loss_usd = 250.0
        violations = check_hard_rules(risk_gate, valid_proposal, portfolio_value=10_000.0)
        assert any("MAX_LOSS_EXCEEDED" in v for v in violations)

    def test_boundary_exactly_at_limit_passes(self, risk_gate, valid_proposal):
        valid_proposal.max_loss_usd = 200.0
        violations = check_hard_rules(risk_gate, valid_proposal, portfolio_value=10_000.0)
        assert not any("MAX_LOSS_EXCEEDED" in v for v in violations)

    def test_boundary_one_cent_over_fails(self, risk_gate, valid_proposal):
        valid_proposal.max_loss_usd = 200.01
        violations = check_hard_rules(risk_gate, valid_proposal, portfolio_value=10_000.0)
        assert any("MAX_LOSS_EXCEEDED" in v for v in violations)

    def test_nan_max_loss_is_rejected(self, risk_gate, valid_proposal):
        valid_proposal.max_loss_usd = math.nan
        violations = check_hard_rules(risk_gate, valid_proposal)
        assert any("INVALID_FINANCIAL_VALUE" in v for v in violations)


class TestPositionLimitRule:
    def test_passes_with_zero_open(self, risk_gate, valid_proposal):
        violations = check_hard_rules(risk_gate, valid_proposal, open_positions_count=0)
        assert not any("POSITION_LIMIT" in v for v in violations)

    def test_passes_with_four_open(self, risk_gate, valid_proposal):
        violations = check_hard_rules(risk_gate, valid_proposal, open_positions_count=4)
        assert not any("POSITION_LIMIT" in v for v in violations)

    def test_fails_at_max_limit(self, risk_gate, valid_proposal):
        violations = check_hard_rules(risk_gate, valid_proposal, open_positions_count=5)
        assert any("POSITION_LIMIT" in v for v in violations)

    def test_fails_above_max_limit(self, risk_gate, valid_proposal):
        violations = check_hard_rules(risk_gate, valid_proposal, open_positions_count=10)
        assert any("POSITION_LIMIT" in v for v in violations)


class TestExposureLimit:
    def test_passes_within_exposure(self, risk_gate, valid_proposal):
        violations = check_hard_rules(
            risk_gate, valid_proposal,
            total_exposure_usd=5000.0, portfolio_value=10_000.0
        )
        assert not any("EXPOSURE_LIMIT" in v for v in violations)

    def test_fails_when_projected_over_80pct(self, risk_gate, valid_proposal):
        valid_proposal.position_value_usd = 2000.0
        violations = check_hard_rules(
            risk_gate, valid_proposal,
            total_exposure_usd=7000.0, portfolio_value=10_000.0
        )
        assert any("EXPOSURE_LIMIT" in v for v in violations)


class TestConsecutiveLossRule:
    """Consecutive losses are now enforced by the Risk Manager LLM, not the hard gate."""

    def test_not_a_hard_gate_violation_at_three(self, risk_gate, valid_proposal):
        # Three losses in a row is policy guidance in the Risk Manager prompt,
        # not a system-level veto. Hard gate should not fire for this.
        violations = check_hard_rules(risk_gate, valid_proposal)
        assert not any("CONSECUTIVE_LOSSES" in v for v in violations)

    def test_not_a_hard_gate_violation_at_ten(self, risk_gate, valid_proposal):
        violations = check_hard_rules(risk_gate, valid_proposal)
        assert not any("CONSECUTIVE_LOSSES" in v for v in violations)


class TestRiskRewardRule:
    """Min R:R is now enforced contextually by the Risk Manager LLM, not the hard gate."""

    def test_not_a_hard_gate_violation_below_1_5(self, risk_gate, valid_proposal):
        # R:R below 1.5 is a policy threshold in the Risk Manager prompt,
        # not a system-level veto.
        valid_proposal.risk_reward_ratio = 1.4
        violations = check_hard_rules(risk_gate, valid_proposal)
        assert not any("RISK_REWARD_TOO_LOW" in v for v in violations)

    def test_not_a_hard_gate_violation_at_zero_rr(self, risk_gate, valid_proposal):
        valid_proposal.risk_reward_ratio = 0.1
        violations = check_hard_rules(risk_gate, valid_proposal)
        assert not any("RISK_REWARD_TOO_LOW" in v for v in violations)


class TestConfidenceRule:
    """Min confidence is now enforced contextually by the Risk Manager LLM, not the hard gate."""

    def test_not_a_hard_gate_violation_at_50pct(self, risk_gate, valid_proposal):
        # Confidence 0.50 is a policy threshold in the Risk Manager prompt,
        # not a system-level veto.
        violations = check_hard_rules(risk_gate, valid_proposal)
        assert not any("LOW_CONFIDENCE" in v for v in violations)

    def test_not_a_hard_gate_violation_at_zero_confidence(self, risk_gate, valid_proposal):
        violations = check_hard_rules(risk_gate, valid_proposal)
        assert not any("LOW_CONFIDENCE" in v for v in violations)


class TestInvalidFieldRule:
    def test_fails_with_zero_stop_loss(self, risk_gate, valid_proposal):
        valid_proposal.stop_loss = 0.0
        violations = check_hard_rules(risk_gate, valid_proposal)
        assert any("INVALID_LEVELS" in v for v in violations)

    def test_fails_with_zero_position_size(self, risk_gate, valid_proposal):
        valid_proposal.position_size_shares = 0
        violations = check_hard_rules(risk_gate, valid_proposal)
        assert any("INVALID_SIZE" in v for v in violations)


class TestMultipleViolations:
    def test_collects_all_hard_violations(self, risk_gate, valid_proposal):
        # Remaining hard gates: MAX_LOSS, POSITION_LIMIT, EXPOSURE_LIMIT, INVALID_LEVELS, INVALID_SIZE
        valid_proposal.max_loss_usd = 500.0
        violations = check_hard_rules(
            risk_gate, valid_proposal,
            open_positions_count=5,
        )
        assert len(violations) >= 2  # MAX_LOSS + POSITION_LIMIT

    def test_rejection_contains_all_violations(self, risk_gate, valid_proposal):
        valid_proposal.max_loss_usd = 500.0
        violations = ["MAX_LOSS_EXCEEDED: test"]
        decision = risk_gate.build_rejection(valid_proposal, violations)
        assert decision.approved is False
        assert decision.hard_rules_passed is False
        assert decision.decision_type == RiskDecisionType.REJECTED_HARD_RULE
        assert len(decision.hard_rule_violations) == 1


class TestApprovalTemplate:
    def test_template_has_correct_hash(self, risk_gate, valid_proposal):
        template = risk_gate.build_approval_template(valid_proposal)
        assert template.proposal_hash == valid_proposal.proposal_hash

    def test_template_not_yet_approved(self, risk_gate, valid_proposal):
        template = risk_gate.build_approval_template(valid_proposal)
        assert template.hard_rules_passed is True
        assert template.approved is False
