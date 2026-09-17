"""Phase 2C: controlled orchestration over normalized Tax Secretarial results."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Mapping

from core.adapter import AdaptedResult, adapt_result_with_source
from core.contracts import AgentResult


@dataclass
class OrchestrationResult:
    """Aggregated normalized results while preserving domain payloads."""

    entity: str
    results: List[AdaptedResult] = field(default_factory=list)

    @property
    def ready(self) -> bool:
        return bool(self.results) and all(
            item.result.status == "READY" for item in self.results
        )

    @property
    def review_required(self) -> bool:
        return any(
            item.result.status == "REVIEW_REQUIRED"
            for item in self.results
        )

    @property
    def missing_data(self) -> List[str]:
        values = []
        for item in self.results:
            values.extend(item.result.missing_data)
        return list(dict.fromkeys(values))

    @property
    def warnings(self) -> List[str]:
        values = []
        for item in self.results:
            values.extend(item.result.warnings)
        return list(dict.fromkeys(values))

    @property
    def evidence(self):
        values = []
        for item in self.results:
            values.extend(item.result.evidence)
        return values

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity": self.entity,
            "status": (
                "READY"
                if self.ready
                else "REVIEW_REQUIRED"
                if self.review_required
                else "NO_RESULTS"
            ),
            "results": [item.result.to_dict() for item in self.results],
            "missing_data": self.missing_data,
            "warnings": self.warnings,
            "evidence": [item.to_dict() for item in self.evidence],
        }


def orchestrate_results(
    entity: str,
    results: Iterable[Any],
) -> OrchestrationResult:
    """Normalize and aggregate existing agent results."""

    normalized = [
        adapt_result_with_source(value, entity=entity)
        for value in results
    ]

    return OrchestrationResult(
        entity=entity,
        results=normalized,
    )


def run_agents(
    entity: str,
    agents: Mapping[str, Callable[[str], Any]],
) -> OrchestrationResult:
    """Execute supplied agent callables and normalize their outputs.

    Agent execution remains outside the orchestration contract; callers
    explicitly provide the agents to run.
    """

    results = []

    for agent_name, agent in agents.items():
        value = agent(entity)
        results.append(
            adapt_result_with_source(
                value,
                agent=agent_name,
                entity=entity,
            )
        )

    return OrchestrationResult(
        entity=entity,
        results=results,
    )
