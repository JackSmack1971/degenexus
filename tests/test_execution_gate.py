"""Tests for ExecutionGate — the hard wall ensuring no execution without valid approval."""

import pytest
from datetime import datetime, timezone, timedelta

from src.core.execution_gate import ExecutionGate, TradeBlockedError
from src.models.signals import RiskDecision, RiskDecisionType


class TestNoApproval:
    def test_raises_when_risk_decision_is_none(self, valid_proposal):
        gate = ExecutionGate()
        with pytest.raises(TradeBlockedError) as exc:
            gate.validate(valid_proposal, None)
        assert "No RiskDecision" in str(exc.value)

    def test_is_clear_returns_false_for_none(self, valid_proposal):
        gate = ExecutionGate()
        clear, reason = gate.is_clear(valid_proposal, None)
        assert clear is False
        assert "No RiskDecision" in reason


class TestRejectedDecision:
    def test_raises_when_approved_is_false(self, valid_proposal, valid_risk_decision):
        gate = ExecutionGate()
        valid_risk_decision.approved = False
        valid_risk_decision.risk_reasoning = "Risk too high"
        with pytest.raises(TradeBlockedError) as exc:
            gate.validate(valid_proposal, valid_risk_decision)
        assert "Risk veto" in str(exc.value)

    def test_raises_when_hard_rules_failed(self, valid_proposal, valid_risk_decision):
        gate = ExecutionGate()
        valid_risk_decision.hard_rules_passed = False
        with pytest.raises(TradeBlockedError) as exc:
            gate.validate(valid_proposal, valid_risk_decision)
        assert "Hard rule" in str(exc.value)


class TestHashMismatch:
    def test_raises_when_hash_does_not_match(self, valid_proposal, valid_risk_decision):
        gate = ExecutionGate()
        valid_risk_decision.proposal_hash = "wrong_hash_00000000"
        with pytest.raises(TradeBlockedError) as exc:
            gate.validate(valid_proposal, valid_risk_decision)
        assert "hash mismatch" in str(exc.value).lower()

    def test_cannot_reuse_approval_for_different_proposal(self, valid_proposal, valid_risk_decision):
        """Critical: approval signed for proposal A cannot be used for proposal B."""
        gate = ExecutionGate()
        proposal_b = valid_proposal.model_copy(deep=True)
        proposal_b.position_size_shares = 99
        proposal_b.proposal_hash = proposal_b.compute_hash()

        with pytest.raises(TradeBlockedError) as exc:
            gate.validate(proposal_b, valid_risk_decision)
        assert "hash mismatch" in str(exc.value).lower()


class TestExpiredDecision:
    def test_raises_when_decision_expired(self, valid_proposal, valid_risk_decision):
        gate = ExecutionGate()
        valid_risk_decision.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        with pytest.raises(TradeBlockedError) as exc:
            gate.validate(valid_proposal, valid_risk_decision)
        assert "expired" in str(exc.value).lower()

    def test_passes_when_decision_not_yet_expired(self, valid_proposal, valid_risk_decision):
        gate = ExecutionGate()
        valid_risk_decision.expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        gate.validate(valid_proposal, valid_risk_decision)


class TestValidApproval:
    def test_passes_all_checks_for_valid_decision(self, valid_proposal, valid_risk_decision):
        gate = ExecutionGate()
        gate.validate(valid_proposal, valid_risk_decision)

    def test_is_clear_returns_true(self, valid_proposal, valid_risk_decision):
        gate = ExecutionGate()
        clear, reason = gate.is_clear(valid_proposal, valid_risk_decision)
        assert clear is True
        assert reason == "CLEAR"


class TestCEOCannotBypass:
    """CEO cannot override the gate by any mechanism."""

    def test_gate_blocks_even_if_called_directly(self, valid_proposal, valid_risk_decision):
        """Simulate CEO trying to call gate.validate with a mocked approval."""
        gate = ExecutionGate()
        # Even if CEO builds a custom RiskDecision with wrong hash, gate blocks it
        ceo_fake_approval = RiskDecision(
            proposal_id=valid_proposal.proposal_id,
            proposal_hash="ceo_bypass_attempt",
            approved=True,
            decision_type=RiskDecisionType.APPROVED,
            hard_rules_passed=True,
            risk_score=1.0,
            risk_reasoning="CEO override",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        )
        with pytest.raises(TradeBlockedError):
            gate.validate(valid_proposal, ceo_fake_approval)
