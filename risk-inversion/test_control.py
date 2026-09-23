import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from risk_inversion.models import ActionDecision, ControlStatus, Evidence, RuntimeIntent
from risk_inversion.control import authorize_intent, can_promote, evaluate_golden_case
from risk_inversion.governance import AuditChain, AuditEvent
from risk_inversion.memory import MemoryNode, reconstruct


def evidence():
    return [Evidence("e1", "test_result", "unit", "control works", ControlStatus.WORKS)]


def test_expired_intent_denied():
    intent = RuntimeIntent("human", "agent-1", "read_customer", "crm", "read", "customer:read", "2000-01-01T00:00:00Z", "test")
    decision = authorize_intent(intent, allowed_intents=["read_customer"], allowed_actions=["read"])
    assert decision.decision is ActionDecision.DENY


def test_kill_switch_denies():
    intent = RuntimeIntent("human", "agent-1", "read_customer", "crm", "read", "customer:read", "2999-01-01T00:00:00Z", "test")
    decision = authorize_intent(intent, allowed_intents=["read_customer"], allowed_actions=["read"], kill_switch=True)
    assert decision.decision is ActionDecision.KILL


def test_golden_case_and_promotion_require_evidence():
    assert evaluate_golden_case({"a": 1}, {"a": 1})
    assert can_promote(ControlStatus.WORKS, evidence())
    assert not can_promote(ControlStatus.WORKS, [])


def test_audit_chain_verifies():
    chain = AuditChain()
    chain.append(AuditEvent("1", "agent-1", "READ", "crm", "ALLOW", "SOP-016"))
    chain.append(AuditEvent("2", "human", "OVERRIDE", "agent-1", "KILL", "SOP-020"))
    assert chain.verify()


def test_memory_reconstruction_tracks_pruning():
    nodes = [
        MemoryNode("1", "invoice", ("finance",), "doc:1", "ledger"),
        MemoryNode("2", "customer", ("crm",), "doc:2", "crm"),
    ]
    result = reconstruct("invoice", nodes, ["finance"])
    assert result.selected_nodes == ("1",)
    assert result.pruned_nodes == ("2",)
