"""Thin brand risk-liaison contract.

Brand repositories can implement this contract without owning Holding policy.
The liaison reports facts/evidence upward; it cannot self-certify VERIFIED/LIVE.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class RiskSignal:
    brand: str
    source: str
    signal: str
    severity: str
    evidence_ids: tuple[str, ...] = ()
    escalation_required: bool = False


@dataclass
class RiskLiaison:
    brand: str
    signals: list[RiskSignal] = field(default_factory=list)

    def report(self, signal: RiskSignal) -> RiskSignal:
        if signal.brand != self.brand:
            raise ValueError("signal brand does not match liaison")
        self.signals.append(signal)
        return signal

    def critical(self) -> list[RiskSignal]:
        return [s for s in self.signals if s.severity == "CRITICAL"]
