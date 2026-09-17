from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    source: str
    claim: str
    status: str = "UNVERIFIED"
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentResult:
    agent: str
    status: str
    entity: str
    summary: str = ""
    missing_data: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    evidence: List[EvidenceItem] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["evidence"] = [
            item.to_dict() if isinstance(item, EvidenceItem) else item
            for item in self.evidence
        ]
        return result
