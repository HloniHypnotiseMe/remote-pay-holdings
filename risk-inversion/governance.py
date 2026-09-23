"""AI governance register and append-only audit contracts."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib, json

@dataclass
class AgentRegisterEntry:
    agent_id: str
    owner: str
    purpose: str
    capabilities: list[str]
    data_classes: list[str]
    connected_systems: list[str]
    risk_class: str
    human_accountable_owner: str
    control_status: str = "EXISTS"
    evaluation_status: str = "NOT_EVALUATED"
    evidence_ids: list[str] = field(default_factory=list)

@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    actor: str
    action: str
    target: str
    decision: str
    policy_id: str
    evidence_id: str | None = None
    occurred_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class AuditChain:
    """Tamper-evident hash chaining; durable append-only storage is separate work."""
    def __init__(self):
        self._events: list[tuple[AuditEvent, str]] = []

    def append(self, event: AuditEvent) -> str:
        previous = self._events[-1][1] if self._events else "GENESIS"
        payload = json.dumps(asdict(event), sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256((previous + payload).encode()).hexdigest()
        self._events.append((event, digest))
        return digest

    def verify(self) -> bool:
        previous = "GENESIS"
        for event, digest in self._events:
            payload = json.dumps(asdict(event), sort_keys=True, separators=(",", ":"))
            expected = hashlib.sha256((previous + payload).encode()).hexdigest()
            if expected != digest:
                return False
            previous = digest
        return True

    @property
    def events(self):
        return tuple(self._events)
