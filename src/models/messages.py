"""All inter-agent message schemas. Every agent-to-agent communication must use these types."""

from __future__ import annotations
from enum import Enum
from typing import Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid


class AgentID(str, Enum):
    CEO = "CEO"
    DATA_ANALYST = "DATA_ANALYST"
    QUANT = "QUANT"
    RISK_MANAGER = "RISK_MANAGER"
    EXECUTION = "EXECUTION"
    PORTFOLIO_MANAGER = "PORTFOLIO_MANAGER"
    MEMORY_SYSTEM = "MEMORY_SYSTEM"


class MessageType(str, Enum):
    SIGNAL = "SIGNAL"
    PROPOSAL = "PROPOSAL"
    RISK_DECISION = "RISK_DECISION"
    CHALLENGE = "CHALLENGE"
    CHALLENGE_RESPONSE = "CHALLENGE_RESPONSE"
    EXECUTION_REPORT = "EXECUTION_REPORT"
    POSITION_UPDATE = "POSITION_UPDATE"
    PERFORMANCE_CONTEXT = "PERFORMANCE_CONTEXT"
    CEO_DIRECTIVE = "CEO_DIRECTIVE"
    HOLD = "HOLD"
    ERROR = "ERROR"


class AgentMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender: AgentID
    recipient: AgentID
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message_type: MessageType
    session_id: str
    payload: Any

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)


class HoldMessage(BaseModel):
    """Emitted when any agent or gate determines no action should be taken."""
    reason: str
    source: AgentID
    cycle_id: str
    safe_action: str = "HOLD"
