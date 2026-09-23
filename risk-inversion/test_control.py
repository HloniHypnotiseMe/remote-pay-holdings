import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).parent
PKG = "holding_risk_inversion"

if PKG not in sys.modules:
    import types
    pkg = types.ModuleType(PKG)
    pkg.__path__ = [str(ROOT)]
    sys.modules[PKG] = pkg


def load(name):
    module_name = f"{PKG}.{name}"
    spec = importlib.util.spec_from_file_location(module_name, ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


models = load("models")
control = load("control")
governance = load("governance")
memory = load("memory")


def evidence():
    return [models.Evidence("e1", "test_result", "unit", "control works", models.ControlStatus.WORKS)]


def test_expired_intent_denied():
    intent = models.RuntimeIntent("human", "agent-1", "read_customer", "crm", "read", "customer:read", "2000-01-01T00:00:00Z", "test")
    decision = control.authorize_intent(intent, allowed_intents=["read_customer"], allowed_actions=["read"])
    assert decision.decision is models.ActionDecision.DENY


def test_kill_switch_denies():
    intent = models.RuntimeIntent("human", "agent-1", "read_customer", "crm", "read", "customer:read", "2999-01-01T00:00:00Z", "test")
    decision = control.authorize_intent(intent, allowed_intents=["read_customer"], allowed_actions=["read"], kill_switch=True)
    assert decision.decision is models.ActionDecision.KILL


def test_golden_case_and_promotion_require_evidence():
    assert control.evaluate_golden_case({"a": 1}, {"a": 1})
    assert control.can_promote(models.ControlStatus.WORKS, evidence())
    assert not control.can_promote(models.ControlStatus.WORKS, [])


def test_audit_chain_verifies():
    chain = governance.AuditChain()
    chain.append(governance.AuditEvent("1", "agent-1", "READ", "crm", "ALLOW", "SOP-016"))
    chain.append(governance.AuditEvent("2", "human", "OVERRIDE", "agent-1", "KILL", "SOP-020"))
    assert chain.verify()


def test_memory_reconstruction_tracks_pruning():
    nodes = [
        memory.MemoryNode("1", "invoice", ("finance",), "doc:1", "ledger"),
        memory.MemoryNode("2", "customer", ("crm",), "doc:2", "crm"),
    ]
    result = memory.reconstruct("invoice", nodes, ["finance"])
    assert result.selected_nodes == ("1",)
    assert result.pruned_nodes == ("2",)
