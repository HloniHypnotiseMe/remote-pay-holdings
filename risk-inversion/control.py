"""Pure, dependency-light control logic for Holding governance.

These controls are intentionally local and deterministic. They do not pretend to
be a production credential broker, immutable ledger, or legal compliance engine.
Those require runtime integrations and independent evidence.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Iterable

from .models import (
    ActionDecision,
    AuthorizationDecision,
    ControlStatus,
    Evidence,
    HumanOverride,
    RuntimeIntent,
)


def _hash_intent(intent: RuntimeIntent) -> str:
    payload = json.dumps(intent.__dict__, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def authorize_intent(
    intent: RuntimeIntent,
    *,
    allowed_intents: Iterable[str],
    allowed_actions: Iterable[str],
    policy_id: str = "SOP-016",
    kill_switch: bool = False,
) -> AuthorizationDecision:
    intent_hash = _hash_intent(intent)
    if kill_switch:
        return AuthorizationDecision(ActionDecision.KILL, "runtime kill switch is active", policy_id, intent_hash)

    try:
        expiry = datetime.fromisoformat(intent.expires_at.replace("Z", "+00:00"))
        if expiry <= datetime.now(timezone.utc):
            return AuthorizationDecision(ActionDecision.DENY, "intent credential expired", policy_id, intent_hash)
    except ValueError:
        return AuthorizationDecision(ActionDecision.DENY, "invalid intent expiry", policy_id, intent_hash)

    if intent.intent not in set(allowed_intents):
        return AuthorizationDecision(ActionDecision.DENY, "intent is not allowed by policy", policy_id, intent_hash)

    if intent.action not in set(allowed_actions):
        return AuthorizationDecision(ActionDecision.DENY, "action is not allowed by policy", policy_id, intent_hash)

    return AuthorizationDecision(ActionDecision.ALLOW, "intent and action authorized", policy_id, intent_hash)


def evaluate_golden_case(expected, actual) -> bool:
    """Deterministic baseline comparator; domain-specific evaluators can extend it."""
    return expected == actual


def can_promote(status: ControlStatus, evidence: list[Evidence]) -> bool:
    return status in {ControlStatus.WORKS, ControlStatus.VERIFIED, ControlStatus.LIVE} and bool(evidence)


def execute_human_override(override: HumanOverride) -> HumanOverride:
    if not override.approved_by_human:
        raise PermissionError("human approval is required")
    override.executed = True
    return override
