"""
EXECUTION GATE — Hard wall between decision and execution.

NO trade can be executed without a valid, unexpired RiskDecision with approved=True
AND a matching proposal_hash. This is enforced in code, not in prompts.

The proposal_hash check prevents CEO from approving proposal A,
then swapping in proposal B and reusing the old approval.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.signals import TradeProposal, RiskDecision


class TradeBlockedError(Exception):
    """Raised when execution is blocked by the gate."""

    def __init__(self, reason: str, proposal_id: str = "", decision_id: str = "") -> None:
        self.reason = reason
        self.proposal_id = proposal_id
        self.decision_id = decision_id
        super().__init__(f"[TRADE_BLOCKED] {reason}")


class ExecutionGate:
    """
    The only path to execution. validate() must return True before
    ExecutionAgent can call _place_order(). No exceptions.

    This gate cannot be bypassed by:
    - CEO instructions
    - Prompt injections
    - Any agent output
    - Missing parameters (None input raises)
    """

    def validate(
        self,
        proposal: "TradeProposal",
        risk_decision: "RiskDecision | None",
    ) -> None:
        """
        Validates that execution is permitted.
        Raises TradeBlockedError on any violation — never returns silently on failure.
        """
        if risk_decision is None:
            raise TradeBlockedError(
                "No RiskDecision provided — execution requires prior Risk Manager approval",
                proposal_id=proposal.proposal_id,
            )

        if not risk_decision.approved:
            raise TradeBlockedError(
                f"Risk veto active: {risk_decision.risk_reasoning}",
                proposal_id=proposal.proposal_id,
                decision_id=risk_decision.decision_id,
            )

        if not risk_decision.hard_rules_passed:
            raise TradeBlockedError(
                f"Hard rule violations: {risk_decision.hard_rule_violations}",
                proposal_id=proposal.proposal_id,
                decision_id=risk_decision.decision_id,
            )

        if risk_decision.proposal_hash != proposal.proposal_hash:
            raise TradeBlockedError(
                "Proposal hash mismatch — risk approval was issued for a different proposal. "
                f"Expected {risk_decision.proposal_hash[:8]}... "
                f"got {proposal.proposal_hash[:8]}...",
                proposal_id=proposal.proposal_id,
                decision_id=risk_decision.decision_id,
            )

        if risk_decision.is_expired:
            raise TradeBlockedError(
                f"RiskDecision expired at {risk_decision.expires_at.isoformat()}",
                proposal_id=proposal.proposal_id,
                decision_id=risk_decision.decision_id,
            )

    def is_clear(
        self,
        proposal: "TradeProposal",
        risk_decision: "RiskDecision | None",
    ) -> tuple[bool, str]:
        """Non-raising wrapper for pre-flight checks."""
        try:
            self.validate(proposal, risk_decision)
            return True, "CLEAR"
        except TradeBlockedError as e:
            return False, e.reason
