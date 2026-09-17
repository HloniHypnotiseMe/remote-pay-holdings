"""Phase 2E: hardened execution of explicit Tax Secretarial case plans."""

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from core.orchestrator import OrchestrationResult, orchestrate_results


@dataclass(frozen=True)
class AgentCall:
    """One explicit call against a real agent instance."""

    agent: str
    method: str
    args: Sequence[Any] = ()
    kwargs: Mapping[str, Any] = None

    def execute(self, agent_instance: Any) -> Any:
        method = getattr(agent_instance, self.method, None)

        if method is None or not callable(method):
            raise AttributeError(
                f"{self.agent}.{self.method} is not a callable agent method."
            )

        return method(*self.args, **(dict(self.kwargs or {})))


def _error_result(entity: str, call: AgentCall, error: Exception) -> Dict[str, Any]:
    """Convert an execution failure into an auditable review result."""

    return {
        "agent": call.agent,
        "status": "REVIEW_REQUIRED",
        "entity": entity,
        "summary": f"{call.agent}.{call.method} failed during case execution.",
        "missing_data": [],
        "warnings": [
            f"{type(error).__name__}: {error}",
        ],
        "evidence": [],
    }


def run_case(
    entity: str,
    calls: Iterable[AgentCall],
    agents: Mapping[str, Any],
) -> OrchestrationResult:
    """Execute a case plan with deterministic failure isolation.

    Each planned agent call is isolated. A failure becomes an explicit
    REVIEW_REQUIRED result rather than silently aborting the entire case.
    """

    if not entity or not str(entity).strip():
        raise ValueError("Case entity is required.")

    raw_results: List[Any] = []

    for call in calls:
        if not call.agent:
            raise ValueError("Case call requires an agent name.")

        if not call.method:
            raise ValueError(
                f"Case call for '{call.agent}' requires a method."
            )

        if call.agent not in agents:
            raise KeyError(
                f"Agent '{call.agent}' is not registered for this case."
            )

        # Invalid method names are case-plan errors and must fail explicitly.
        method = getattr(agents[call.agent], call.method, None)
        if method is None or not callable(method):
            raise AttributeError(
                f"{call.agent}.{call.method} is not a callable agent method."
            )

        try:
            raw = call.execute(agents[call.agent])

            if isinstance(raw, dict):
                raw = dict(raw)
                raw.setdefault("agent", call.agent)
                raw.setdefault("entity", entity)

            raw_results.append(raw)

        except Exception as error:
            raw_results.append(
                _error_result(entity, call, error)
            )

    return orchestrate_results(entity, raw_results)
