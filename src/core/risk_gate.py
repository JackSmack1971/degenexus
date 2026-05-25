"""
RISK GATE — System-level hard veto enforcement.

This is NOT a prompt instruction. Hard rules are enforced in Python.
No LLM, no agent, no CEO can bypass these checks.
If any hard rule fires → REJECTED, period.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING
import os

if TYPE_CHECKING:
    from ..models.signals import TradeProposal, RiskDecision


class HardRuleViolation(Exception):
    """Raised when a trade proposal violates a hard risk rule."""

    def __init__(self, rule: str, detail: str) -> None:
        self.rule = rule
        self.detail = detail
        super().__init__(f"[HARD_RULE_VIOLATION] {rule}: {detail}")


@dataclass
class RiskLimits:
    max_loss_pct_per_trade: float = 0.02
    max_open_positions: int = 5
    max_total_exposure_pct: float = 0.80
    max_consecutive_losses: int = 3
    min_risk_reward: float = 1.5
    min_confidence: float = 0.55
    risk_decision_ttl_seconds: int = 300

    @classmethod
    def from_env(cls) -> "RiskLimits":
        return cls(
            max_loss_pct_per_trade=float(os.getenv("MAX_LOSS_PCT_PER_TRADE", "0.02")),
            max_open_positions=int(os.getenv("MAX_OPEN_POSITIONS", "5")),
            max_total_exposure_pct=float(os.getenv("MAX_TOTAL_EXPOSURE_PCT", "0.80")),
            max_consecutive_losses=int(os.getenv("MAX_CONSECUTIVE_LOSSES", "3")),
            min_risk_reward=float(os.getenv("MIN_RISK_REWARD", "1.5")),
            min_confidence=float(os.getenv("MIN_CONFIDENCE", "0.55")),
        )


class RiskGate:
    """
    System-level risk enforcement. Called before any trade proposal
    reaches the execution gate. Two layers:

    Layer 1 — Hard rules (pure Python, deterministic, instantaneous)
    Layer 2 — Soft assessment passed to LLM Risk Manager agent for context

    This class owns Layer 1. Layer 2 is the risk_manager agent.
    A RiskDecision from Layer 1 failure is FINAL — LLM cannot override it.
    """

    def __init__(self, limits: RiskLimits | None = None) -> None:
        self.limits = limits or RiskLimits.from_env()

    def check_hard_rules(
        self,
        proposal: "TradeProposal",
        portfolio_value: float,
        open_positions_count: int,
        total_exposure_usd: float,
    ) -> list[str]:
        """
        Run all hard rules against the proposal.
        Returns list of violations (empty = all passed).
        Does NOT raise — callers decide whether to halt or log.
        """
        violations: list[str] = []

        max_allowed_loss = portfolio_value * self.limits.max_loss_pct_per_trade
        if proposal.max_loss_usd > max_allowed_loss:
            violations.append(
                f"MAX_LOSS_EXCEEDED: ${proposal.max_loss_usd:.2f} > "
                f"${max_allowed_loss:.2f} ({self.limits.max_loss_pct_per_trade:.1%} of portfolio)"
            )

        if open_positions_count >= self.limits.max_open_positions:
            violations.append(
                f"POSITION_LIMIT: {open_positions_count} open positions "
                f">= limit of {self.limits.max_open_positions}"
            )

        projected_exposure = total_exposure_usd + proposal.position_value_usd
        if projected_exposure / portfolio_value > self.limits.max_total_exposure_pct:
            violations.append(
                f"EXPOSURE_LIMIT: projected {projected_exposure/portfolio_value:.1%} "
                f"> limit {self.limits.max_total_exposure_pct:.1%}"
            )

        if proposal.stop_loss <= 0 or proposal.take_profit <= 0:
            violations.append("INVALID_LEVELS: stop_loss and take_profit must be > 0")

        if proposal.position_size_shares <= 0:
            violations.append("INVALID_SIZE: position_size_shares must be > 0")

        return violations

    def build_rejection(
        self,
        proposal: "TradeProposal",
        violations: list[str],
    ) -> "RiskDecision":
        from ..models.signals import RiskDecision, RiskDecisionType
        from ..models.messages import AgentID

        return RiskDecision(
            proposal_id=proposal.proposal_id,
            proposal_hash=proposal.proposal_hash,
            approved=False,
            decision_type=RiskDecisionType.REJECTED_HARD_RULE,
            hard_rules_passed=False,
            hard_rule_violations=violations,
            risk_score=10.0,
            risk_reasoning="; ".join(violations),
            expires_at=datetime.now(timezone.utc),
        )

    def build_approval_template(self, proposal: "TradeProposal") -> "RiskDecision":
        """
        Returns a partial approval template with hard_rules_passed=True.
        The LLM Risk Manager agent fills in risk_score, risk_reasoning, and
        sets approved=True/False based on contextual assessment.
        """
        from ..models.signals import RiskDecision, RiskDecisionType
        from ..models.messages import AgentID

        return RiskDecision(
            proposal_id=proposal.proposal_id,
            proposal_hash=proposal.proposal_hash,
            approved=False,
            decision_type=RiskDecisionType.APPROVED,
            hard_rules_passed=True,
            risk_score=0.0,
            risk_reasoning="Pending contextual assessment by Risk Manager agent",
            expires_at=datetime.now(timezone.utc) + timedelta(
                seconds=self.limits.risk_decision_ttl_seconds
            ),
        )
