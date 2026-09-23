"""Canonical Holding risk/inversion control contracts."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ControlStatus(str, Enum):
    EXISTS = "EXISTS"
    WORKS = "WORKS"
    VERIFIED = "VERIFIED"
    LIVE = "LIVE"
    GAP = "GAP"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(str, Enum):
    OPEN = "OPEN"
    CONTAINED = "CONTAINED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class ActionDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    ESCALATE = "ESCALATE"
    KILL = "KILL"


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    evidence_type: str
    source: str
    claim: str
    status: ControlStatus = ControlStatus.EXISTS
    captured_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class RiskRecord:
    risk_id: str
    owner: str
    asset: str
    threat: str
    impact: str
    likelihood: str
    severity: Severity
    controls: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    status: ControlStatus = ControlStatus.EXISTS


@dataclass
class InversionCase:
    case_id: str
    objective: str
    assumption: str
    failure_mode: str
    detection_signal: str
    prevention: list[str] = field(default_factory=list)
    recovery: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    status: ControlStatus = ControlStatus.EXISTS


@dataclass(frozen=True)
class RuntimeIntent:
    actor: str
    agent_id: str
    intent: str
    resource: str
    action: str
    credential_scope: str
    expires_at: str
    reason: str


@dataclass(frozen=True)
class AuthorizationDecision:
    decision: ActionDecision
    reason: str
    policy_id: str
    intent_hash: str


@dataclass
class EvaluationCase:
    case_id: str
    dataset: str
    input: Any
    expected: Any
    actual: Any | None = None
    passed: bool | None = None
    evidence: list[Evidence] = field(default_factory=list)


@dataclass
class HumanOverride:
    override_id: str
    requested_by: str
    target: str
    action: ActionDecision
    reason: str
    approved_by_human: bool = False
    executed: bool = False
    evidence: list[Evidence] = field(default_factory=list)
