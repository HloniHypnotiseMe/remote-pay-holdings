"""Phase 2B: normalize existing agent outputs to the shared AgentResult contract."""

from dataclasses import dataclass
from typing import Any, Dict, Mapping

from core.contracts import AgentResult, EvidenceItem


@dataclass(frozen=True)
class AdaptedResult:
    """Normalized contract plus the untouched source result."""

    result: AgentResult
    source: Any


def _evidence_item(value: Any) -> EvidenceItem:
    if isinstance(value, EvidenceItem):
        return value

    if isinstance(value, Mapping):
        allowed = {
            "evidence_id",
            "source",
            "claim",
            "status",
            "notes",
        }
        data = {key: value[key] for key in allowed if key in value}

        required = {"evidence_id", "source", "claim"}
        missing = required - data.keys()
        if missing:
            raise ValueError(
                f"Evidence item missing required fields: {sorted(missing)}"
            )

        return EvidenceItem(**data)

    raise TypeError(f"Unsupported evidence item: {type(value).__name__}")


def _mapping_from(value: Any) -> Dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)

    if hasattr(value, "to_dict") and callable(value.to_dict):
        converted = value.to_dict()
        if isinstance(converted, Mapping):
            return dict(converted)

    raise TypeError(
        "Unsupported agent result. Expected a mapping or object with to_dict()."
    )


def adapt_result(
    value: Any,
    *,
    agent: str | None = None,
    entity: str | None = None,
) -> AgentResult:
    """Convert an existing agent result into the shared AgentResult contract."""

    if isinstance(value, AgentResult):
        return value

    data = _mapping_from(value)

    resolved_agent = agent or data.get("agent")
    resolved_entity = entity or data.get("entity")

    if not resolved_agent:
        raise ValueError("AgentResult adaptation requires an agent name.")
    if not resolved_entity:
        raise ValueError("AgentResult adaptation requires an entity.")

    evidence = [
        _evidence_item(item)
        for item in data.get("evidence", [])
    ]

    return AgentResult(
        agent=str(resolved_agent),
        status=str(data.get("status", "REVIEW_REQUIRED")),
        entity=str(resolved_entity),
        summary=str(data.get("summary", "")),
        missing_data=list(data.get("missing_data", [])),
        warnings=list(data.get("warnings", [])),
        evidence=evidence,
    )


def adapt_result_with_source(
    value: Any,
    *,
    agent: str | None = None,
    entity: str | None = None,
) -> AdaptedResult:
    """Normalize a result while retaining the original domain payload."""

    return AdaptedResult(
        result=adapt_result(value, agent=agent, entity=entity),
        source=value,
    )
