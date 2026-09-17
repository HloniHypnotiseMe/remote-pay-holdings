from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.win_event import emit_win_event

from config.tax_config import (
    SBC_BANDS,
    SBC_GROSS_INCOME_LIMIT,
    TURNOVER_TAX_BANDS,
    TURNOVER_TAX_THRESHOLD,
)
from core.contracts import EvidenceItem


@dataclass
class SBCEligibility:
    eligible: Optional[bool]
    status: str
    missing_data: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    evidence: List[EvidenceItem] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["evidence"] = [item.to_dict() for item in self.evidence]
        return result


@dataclass
class ReviewResult:
    entity: str
    status: str
    tax_regime: str
    accounting_profit: Optional[float]
    taxable_income: Optional[float]
    turnover: Optional[float]
    estimated_tax: Optional[float]
    missing_data: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    evidence: List[EvidenceItem] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["evidence"] = [item.to_dict() for item in self.evidence]
        return result


class TaxDirector:
    agent_name = "tax_director"

    @staticmethod
    def calculate_sbc_tax(taxable_income: float) -> float:
        if taxable_income < 0:
            raise ValueError("Taxable income cannot be negative.")

        for lower, upper, base, rate in SBC_BANDS:
            if upper is None or taxable_income <= upper:
                return round(base + max(0, taxable_income - lower) * rate, 2)

        raise ValueError("Unable to calculate SBC tax.")

    @staticmethod
    def calculate_cit(taxable_income: float) -> float:
        if taxable_income < 0:
            raise ValueError("Taxable income cannot be negative.")
        return round(taxable_income * 0.27, 2)

    @staticmethod
    def calculate_turnover_tax(turnover: float) -> float:
        if turnover < 0:
            raise ValueError("Turnover cannot be negative.")

        if turnover > TURNOVER_TAX_THRESHOLD:
            raise ValueError(
                f"Turnover exceeds turnover-tax threshold of "
                f"R{TURNOVER_TAX_THRESHOLD:,.0f}."
            )

        for lower, upper, base, rate in TURNOVER_TAX_BANDS:
            if upper is None or turnover <= upper:
                return round(base + max(0, turnover - lower) * rate, 2)

        raise ValueError("Unable to calculate turnover tax.")

    @staticmethod
    def evaluate_sbc_eligibility(
        *,
        gross_income: Optional[float],
        all_shareholders_natural_persons: Optional[bool],
        personal_service_company: Optional[bool],
        holding_company: Optional[bool],
    ) -> SBCEligibility:

        missing = []
        blockers = []
        evidence = []

        if gross_income is None:
            missing.append("gross_income")
        else:
            evidence.append(
                EvidenceItem(
                    evidence_id="SBC-GROSS-INCOME",
                    source="entity_input",
                    claim=f"Gross income supplied: R{gross_income:,.2f}",
                    status="SUPPLIED",
                )
            )

            if gross_income > SBC_GROSS_INCOME_LIMIT:
                blockers.append(
                    f"Gross income exceeds SBC limit of "
                    f"R{SBC_GROSS_INCOME_LIMIT:,.0f}."
                )

        checks = {
            "all_shareholders_natural_persons": all_shareholders_natural_persons,
            "personal_service_company": personal_service_company,
            "holding_company": holding_company,
        }

        for field_name, value in checks.items():
            if value is None:
                missing.append(field_name)
                continue

            evidence.append(
                EvidenceItem(
                    evidence_id=f"SBC-{field_name.upper()}",
                    source="entity_input",
                    claim=f"{field_name}={value}",
                    status="SUPPLIED",
                )
            )

        if all_shareholders_natural_persons is False:
            blockers.append("Not all shareholders/members are natural persons.")

        if personal_service_company is True:
            blockers.append("Entity is identified as a personal service company.")

        if holding_company is True:
            blockers.append("Entity is identified as a holding company.")

        if blockers:
            return SBCEligibility(
                eligible=False,
                status="BLOCKED",
                missing_data=missing,
                blockers=blockers,
                evidence=evidence,
            )

        if missing:
            return SBCEligibility(
                eligible=None,
                status="REVIEW_REQUIRED",
                missing_data=missing,
                evidence=evidence,
            )

        return SBCEligibility(
            eligible=True,
            status="READY",
            evidence=evidence,
        )

    def review_entity(
        self,
        entity: str,
        *,
        accounting_profit: Optional[float] = None,
        taxable_income: Optional[float] = None,
        turnover: Optional[float] = None,
        tax_regime: Optional[str] = None,
        gross_income: Optional[float] = None,
        all_shareholders_natural_persons: Optional[bool] = None,
        personal_service_company: Optional[bool] = None,
        holding_company: Optional[bool] = None,
    ) -> ReviewResult:

        # Backward-compatible input contract:
        # older callers may pass the complete entity record as one dictionary.
        if isinstance(entity, dict):
            record = entity
            entity = record.get("entity", "")
            accounting_profit = record.get("accounting_profit")
            taxable_income = record.get("taxable_income")
            turnover = record.get("turnover")
            tax_regime = record.get("tax_regime")
            gross_income = record.get("gross_income")
            all_shareholders_natural_persons = record.get(
                "all_shareholders_natural_persons"
            )
            personal_service_company = record.get("personal_service_company")
            holding_company = record.get("holding_company")

        missing = []
        warnings = []
        evidence = []

        if not tax_regime:
            missing.append("tax_regime")

        if taxable_income is None:
            missing.append("taxable_income")

        estimated_tax = None

        if tax_regime == "sbc":
            eligibility = self.evaluate_sbc_eligibility(
                gross_income=gross_income,
                all_shareholders_natural_persons=all_shareholders_natural_persons,
                personal_service_company=personal_service_company,
                holding_company=holding_company,
            )

            evidence.extend(eligibility.evidence)

            # SBC eligibility fields are required only for the SBC regime.
            # They must never affect CIT or turnover-tax calculations.
            missing.extend(eligibility.missing_data)

            if eligibility.status == "BLOCKED":
                warnings.extend(eligibility.blockers)

            elif eligibility.status == "REVIEW_REQUIRED":
                warnings.append("SBC eligibility requires additional evidence.")

            if taxable_income is not None and eligibility.eligible is True:
                estimated_tax = self.calculate_sbc_tax(taxable_income)

        elif tax_regime in ("cit", "standard_cit"):
            if taxable_income is not None:
                estimated_tax = self.calculate_cit(taxable_income)

        elif tax_regime == "turnover_tax":
            if turnover is None:
                missing.append("turnover")
            else:
                try:
                    estimated_tax = self.calculate_turnover_tax(turnover)
                except ValueError as exc:
                    warnings.append(str(exc))

        elif tax_regime:
            warnings.append(f"Unsupported tax regime: {tax_regime}")

        if accounting_profit is not None and taxable_income is not None:
            if accounting_profit != taxable_income:
                warnings.append(
                    "Accounting profit differs from taxable income; "
                    "tax adjustments/evidence must be reconciled."
                )

        if missing:
            status = "REVIEW_REQUIRED"
        elif any("exceeds" in warning.lower() for warning in warnings):
            status = "BLOCKED"
        elif tax_regime == "sbc" and any(
            "eligibility" in warning.lower() for warning in warnings
        ):
            status = "REVIEW_REQUIRED"
        elif estimated_tax is None:
            status = "REVIEW_REQUIRED"
        else:
            status = "READY"

        evidence.append(
            EvidenceItem(
                evidence_id="TAX-REVIEW",
                source=self.agent_name,
                claim=f"Tax review prepared for {entity}.",
                status="PREPARED",
                notes="Preparation only; no filing or submission performed.",
            )
        )

        result = ReviewResult(
            entity=entity,
            status=status,
            tax_regime=tax_regime or "",
            accounting_profit=accounting_profit,
            taxable_income=taxable_income,
            turnover=turnover,
            estimated_tax=estimated_tax,
            missing_data=sorted(set(missing)),
            warnings=warnings,
            evidence=evidence,
        )

        emit_win_event({
            "objective": "Produce an evidence-backed tax review",
            "minimum_winnable_action": "Complete one entity review with required tax inputs",
            "proof_required": "READY_FOR_REVIEW result with explicit evidence",
            "project": "Tax Secretarial",
            "actor": "tax_director",
            "tier": "EXECUTION",
            "evidence": {
                "event": "tax_review_completed",
                "entity": entity,
                "status": result.status,
                "tax_regime": regime,
                "estimated_tax": result.estimated_tax,
                "evidence_count": len(result.evidence),
            },
            "capability_unlocked": "Evidence-backed tax review",
            "next_win": "Complete the next compliance obligation with evidence",
        })

        return result

    def review_file(
        self,
        path: str | Path,
        output_path: Optional[str] = None,
        **kwargs: Any,
    ) -> ReviewResult:

        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(path)

        with file_path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            data = json.load(handle)

        # Preserve the original file-driven contract while allowing
        # optional review overrides for newer callers.
        if kwargs:
            data = {
                **data,
                **kwargs,
            }

        result = self.review_entity(data)

        destination = None

        if output_path:
            destination = Path(output_path)
        elif self.evidence_dir:
            self.evidence_dir.mkdir(
                parents=True,
                exist_ok=True,
            )
            destination = (
                self.evidence_dir
                / f"{file_path.stem}.review.json"
            )

        if destination:
            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            destination.write_text(
                json.dumps(result.to_dict(), indent=2),
                encoding="utf-8",
            )

        return result


# ---------------------------------------------------------------------------
# Backward-compatible module-level calculation API
# Existing C6 callers/tests use these functions directly.
# ---------------------------------------------------------------------------

def calculate_sbc_tax(taxable_income: float) -> float:
    return TaxDirector.calculate_sbc_tax(taxable_income)


def calculate_cit(taxable_income: float) -> float:
    return TaxDirector.calculate_cit(taxable_income)


def calculate_turnover_tax(turnover: float) -> float:
    return TaxDirector.calculate_turnover_tax(turnover)
