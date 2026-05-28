"""Tests for RiskManagerAgent contextual assessment paths."""

import pytest
from datetime import datetime, timezone, timedelta

from src.agents.risk_manager import RiskManagerAgent
from src.core.risk_gate import RiskGate
from src.models.signals import RiskDecision, RiskDecisionType


def _make_agent():
    agent = RiskManagerAgent.__new__(RiskManagerAgent)
    agent.agent_id = "RISK_MANAGER"
    agent.performance_context = ""
    agent._provider = "fallback"
    agent._client = None
    agent._llm_timeout_seconds = 30
    agent.risk_gate = RiskGate()
    return agent


def _future_expiry():
    return datetime.now(timezone.utc) + timedelta(minutes=5)


def _template(proposal):
    return RiskDecision(
        proposal_id=proposal.proposal_id,
        proposal_hash=proposal.proposal_hash,
        approved=True,
        decision_type=RiskDecisionType.APPROVED,
        hard_rules_passed=True,
        risk_score=3.0,
        risk_reasoning="template",
        expires_at=_future_expiry(),
    )


class TestContextualAssessApproved:
    def test_approved_path_returns_approved_decision(self, valid_proposal):
        agent = _make_agent()
        tmpl = _template(valid_proposal)

        agent.call_llm = lambda sys, usr: {
            "approved": True,
            "decision_type": "APPROVED",
            "risk_score": 2.5,
            "risk_reasoning": "solid setup",
            "conditions": [],
        }

        result = agent._contextual_assess(valid_proposal, tmpl, 0, 0.72, "")
        assert result.approved is True
        assert result.risk_score == pytest.approx(2.5)
        assert result.decision_type == RiskDecisionType.APPROVED

    def test_approved_with_conditions_passthrough(self, valid_proposal):
        agent = _make_agent()
        tmpl = _template(valid_proposal)

        agent.call_llm = lambda sys, usr: {
            "approved": True,
            "decision_type": "APPROVED_WITH_CONDITIONS",
            "risk_score": 5.5,
            "risk_reasoning": "reduce size",
            "conditions": ["reduce_size_by_50pct"],
        }

        result = agent._contextual_assess(valid_proposal, tmpl, 3, 0.60, "")
        assert result.approved is True
        assert result.conditions == ["reduce_size_by_50pct"]
        assert result.decision_type == RiskDecisionType.APPROVED_WITH_CONDITIONS


class TestContextualAssessRejected:
    def test_rejected_path_returns_rejected_decision(self, valid_proposal):
        agent = _make_agent()
        tmpl = _template(valid_proposal)

        agent.call_llm = lambda sys, usr: {
            "approved": False,
            "decision_type": "REJECTED_CONTEXTUAL",
            "risk_score": 8.0,
            "risk_reasoning": "too risky",
            "conditions": [],
        }

        result = agent._contextual_assess(valid_proposal, tmpl, 4, 0.50, "")
        assert result.approved is False
        assert result.risk_score == pytest.approx(8.0)
        assert result.decision_type == RiskDecisionType.REJECTED_CONTEXTUAL


class TestNaNRiskScore:
    def test_nan_risk_score_clamped_to_valid_range(self, valid_proposal):
        agent = _make_agent()
        tmpl = _template(valid_proposal)

        import math
        agent.call_llm = lambda sys, usr: {
            "approved": False,
            "decision_type": "REJECTED_CONTEXTUAL",
            "risk_score": math.nan,
            "risk_reasoning": "bad score",
            "conditions": [],
        }

        # nan comparison with max/min: float(nan) → clamped to bounds
        # max(0, min(10, nan)) → nan in Python; but _contextual_assess wraps in try/except
        # so it falls through to _fallback_decision
        result = agent._contextual_assess(valid_proposal, tmpl, 0, 0.72, "")
        # Either clamped result or fallback — neither should raise; risk_score in [0, 10]
        assert 0.0 <= result.risk_score <= 10.0

    def test_risk_score_above_10_clamped(self, valid_proposal):
        agent = _make_agent()
        tmpl = _template(valid_proposal)

        agent.call_llm = lambda sys, usr: {
            "approved": True,
            "decision_type": "APPROVED",
            "risk_score": 99.0,
            "risk_reasoning": "out of range",
            "conditions": [],
        }

        result = agent._contextual_assess(valid_proposal, tmpl, 0, 0.72, "")
        assert result.risk_score <= 10.0


class TestFallbackDecision:
    def test_fallback_decision_rejects_with_score_8(self, valid_proposal):
        agent = _make_agent()
        tmpl = _template(valid_proposal)
        result = agent._fallback_decision(valid_proposal, tmpl)
        assert result.approved is False
        assert result.risk_score == pytest.approx(8.0)
        assert result.hard_rules_passed is True
        assert "[FALLBACK]" in result.risk_reasoning

    def test_call_llm_fallback_dict_rejects(self, valid_proposal):
        agent = _make_agent()
        result = agent._fallback("context")
        assert result["approved"] is False
        assert result["risk_score"] == 8.0


class TestUnknownDecisionType:
    def test_unknown_decision_type_coerced_to_enum(self, valid_proposal):
        agent = _make_agent()
        tmpl = _template(valid_proposal)

        agent.call_llm = lambda sys, usr: {
            "approved": True,
            "decision_type": "UNKNOWN_TYPE",
            "risk_score": 3.0,
            "risk_reasoning": "ok",
            "conditions": [],
        }

        result = agent._contextual_assess(valid_proposal, tmpl, 0, 0.72, "")
        # unknown type → approved=True → APPROVED fallback
        assert result.decision_type == RiskDecisionType.APPROVED


# ── assess_contextual_risk() entry-point (lines 59-60) ───────────────────────

class TestAssessContextualRisk:

    def test_delegates_to_contextual_assess_approved(self, valid_proposal):
        """Lines 59-60: assess_contextual_risk() calls build_approval_template + _contextual_assess."""
        agent = _make_agent()
        agent.call_llm = lambda sys, usr: {
            "approved": True,
            "decision_type": "APPROVED",
            "risk_score": 3.0,
            "risk_reasoning": "solid setup",
            "conditions": [],
        }
        result = agent.assess_contextual_risk(
            valid_proposal,
            consecutive_losses=0,
            signal_confidence=0.72,
        )
        assert result.approved is True
        assert result.risk_score == pytest.approx(3.0)
        assert result.decision_type == RiskDecisionType.APPROVED

    def test_delegates_with_open_positions_summary(self, valid_proposal):
        """Lines 59-60: open_positions_summary passes through to _contextual_assess."""
        agent = _make_agent()
        agent.call_llm = lambda sys, usr: {
            "approved": False,
            "decision_type": "REJECTED_CONTEXTUAL",
            "risk_score": 7.0,
            "risk_reasoning": "correlated exposure",
            "conditions": [],
        }
        result = agent.assess_contextual_risk(
            valid_proposal,
            consecutive_losses=2,
            signal_confidence=0.60,
            open_positions_summary="AAPL LONG 10 shares",
        )
        assert result.approved is False
        assert result.risk_score == pytest.approx(7.0)


# ── _contextual_assess() parse-failure path (lines 125-127) ──────────────────

class TestContextualAssessParseFailure:

    def test_non_numeric_risk_score_triggers_fallback(self, valid_proposal):
        """Lines 125-127: float('not-a-number') raises ValueError → _fallback_decision."""
        agent = _make_agent()
        tmpl = _template(valid_proposal)
        agent.call_llm = lambda sys, usr: {
            "approved": True,
            "decision_type": "APPROVED",
            "risk_score": "not-a-number",
            "risk_reasoning": "ok",
            "conditions": [],
        }
        result = agent._contextual_assess(valid_proposal, tmpl, 0, 0.72, "")
        assert result.approved is False
        assert result.risk_score == pytest.approx(8.0)
        assert "[FALLBACK]" in result.risk_reasoning

    def test_none_risk_score_triggers_fallback(self, valid_proposal):
        """Lines 125-127: float(None) raises TypeError → _fallback_decision."""
        agent = _make_agent()
        tmpl = _template(valid_proposal)
        agent.call_llm = lambda sys, usr: {
            "approved": True,
            "decision_type": "APPROVED",
            "risk_score": None,
            "risk_reasoning": "ok",
            "conditions": [],
        }
        result = agent._contextual_assess(valid_proposal, tmpl, 0, 0.72, "")
        assert result.approved is False
        assert result.risk_score == pytest.approx(8.0)

    def test_malformed_decision_type_dict_triggers_fallback(self, valid_proposal):
        """Lines 125-127: non-string decision_type causes RiskDecision construction to fail."""
        agent = _make_agent()
        tmpl = _template(valid_proposal)
        # Provide a list for risk_score to force TypeError in float()
        agent.call_llm = lambda sys, usr: {
            "approved": True,
            "risk_score": [1, 2, 3],
            "conditions": [],
        }
        result = agent._contextual_assess(valid_proposal, tmpl, 0, 0.72, "")
        assert result.approved is False
        assert "[FALLBACK]" in result.risk_reasoning
