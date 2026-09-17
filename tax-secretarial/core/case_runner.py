"""Phase 2D: execute an explicit Tax Secretarial case plan."""

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


def run_case(
    entity: str,
    calls: Iterable[AgentCall],
    agents: Mapping[str, Any],
) -> OrchestrationResult:
    """Execute an explicit case plan against supplied real agent instances.

    The case plan owns domain-specific method selection and arguments.
    The runner owns execution, normalization, and aggregation.
    """

    raw_results: List[Any] = []

    for call in calls:
        if call.agent not in agents:
            raise KeyError(
                f"Agent '{call.agent}' is not registered for this case."
            )

        raw = call.execute(agents[call.agent])

        if isinstance(raw, dict):
            raw = dict(raw)
            raw.setdefault("agent", call.agent)
            raw.setdefault("entity", entity)

        raw_results.append(raw)

    return orchestrate_results(entity, raw_results)
