#!/usr/bin/env python3
"""
C6 Tax Director.

Separates accounting profit from taxable income and requires
explicit tax-regime evidence.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

import sys

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.tax_config import (
    SBC_GROSS_INCOME_LIMIT,
    STANDARD_CIT_RATE,
    TURNOVER_TAX_THRESHOLD,
)


@dataclass
class ReviewResult:
    entity: str
    status: str
    tax_regime: Optional[str]
    accounting_profit: Optional[float]
    taxable_income: Optional[float]
    turnover: Optional[float]
    estimated_tax: Optional[float]
    missing_data: list[str]
    warnings: list[str]
    evidence: list[str]


def calculate_sbc_tax(taxable_income: float) -> float:
    income = max(0.0, float(taxable_income))

    if income <= 99_000:
        return 0.0

    if income <= 365_000:
        return (income - 99_000) * 0.07

    if income <= 550_000:
        return 18_620 + ((income - 365_000) * 0.21)

    return 57_470 + ((income - 550_000) * 0.27)


def calculate_cit(taxable_income: float) -> float:
    return max(0.0, float(taxable_income)) * STANDARD_CIT_RATE


def calculate_turnover_tax(turnover: float) -> float:
    amount = max(0.0, float(turnover))

    if amount <= 600_000:
        return 0.0

    if amount <= 950_000:
        return (amount - 600_000) * 0.01

    if amount <= 1_400_000:
        return 3_500 + ((amount - 950_000) * 0.02)

    if amount <= TURNOVER_TAX_THRESHOLD:
        return 12_500 + ((amount - 1_400_000) * 0.03)

    raise ValueError(
        "Turnover exceeds the configured 2026/27 Turnover Tax threshold."
    )


class TaxDirector:

    def __init__(
        self,
        evidence_dir: Optional[str | Path] = None,
    ):
        self.evidence_dir = (
            Path(evidence_dir)
            if evidence_dir
            else None
        )

    def review_entity(
        self,
        data: dict[str, Any],
    ) -> ReviewResult:

        entity = str(
            data.get("entity", "UNKNOWN")
        )

        accounting_profit = data.get(
            "accounting_profit"
        )

        taxable_income = data.get(
            "taxable_income"
        )

        turnover = data.get(
            "turnover"
        )

        regime = data.get(
            "tax_regime"
        )

        missing = []
        warnings = []
        evidence = []

        if not regime:
            missing.append("tax_regime")

        if taxable_income is None:
            missing.append("taxable_income")

        if regime == "turnover_tax" and turnover is None:
            missing.append("turnover")

        if regime == "sbc":

            if data.get("sbc_eligible") is not True:
                missing.append(
                    "confirmed_sbc_eligibility"
                )

            if data.get("gross_income") is None:
                missing.append(
                    "gross_income"
                )

        if missing:
            return ReviewResult(
                entity=entity,
                status="REVIEW_REQUIRED",
                tax_regime=regime,
                accounting_profit=accounting_profit,
                taxable_income=taxable_income,
                turnover=turnover,
                estimated_tax=None,
                missing_data=missing,
                warnings=warnings,
                evidence=evidence,
            )

        if regime == "standard_cit":

            estimated_tax = calculate_cit(
                taxable_income
            )

        elif regime == "sbc":

            gross_income = float(
                data["gross_income"]
            )

            if gross_income > SBC_GROSS_INCOME_LIMIT:

                return ReviewResult(
                    entity=entity,
                    status="REVIEW_REQUIRED",
                    tax_regime=regime,
                    accounting_profit=accounting_profit,
                    taxable_income=taxable_income,
                    turnover=turnover,
                    estimated_tax=None,
                    missing_data=[],
                    warnings=[
                        "Gross income exceeds SBC eligibility limit."
                    ],
                    evidence=evidence,
                )

            estimated_tax = calculate_sbc_tax(
                taxable_income
            )

        elif regime == "turnover_tax":

            estimated_tax = calculate_turnover_tax(
                turnover
            )

        else:

            return ReviewResult(
                entity=entity,
                status="REVIEW_REQUIRED",
                tax_regime=regime,
                accounting_profit=accounting_profit,
                taxable_income=taxable_income,
                turnover=turnover,
                estimated_tax=None,
                missing_data=[],
                warnings=[
                    f"Unsupported tax regime: {regime}"
                ],
                evidence=evidence,
            )

        if (
            accounting_profit is not None
            and taxable_income != accounting_profit
        ):
            warnings.append(
                "Accounting profit differs from taxable income; "
                "tax calculation uses taxable income supplied by the reviewer."
            )

        evidence.extend([
            "tax_regime explicitly supplied",
            "taxable_income explicitly supplied",
        ])

        return ReviewResult(
            entity=entity,
            status="READY_FOR_REVIEW",
            tax_regime=regime,
            accounting_profit=accounting_profit,
            taxable_income=taxable_income,
            turnover=turnover,
            estimated_tax=round(
                estimated_tax,
                2,
            ),
            missing_data=[],
            warnings=warnings,
            evidence=evidence,
        )

    def review_file(
        self,
        path: str | Path,
    ) -> ReviewResult:

        file_path = Path(path)

        with file_path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            data = json.load(handle)

        result = self.review_entity(data)

        if self.evidence_dir:

            self.evidence_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            output = (
                self.evidence_dir
                / f"{file_path.stem}.review.json"
            )

            with output.open(
                "w",
                encoding="utf-8",
            ) as handle:
                json.dump(
                    asdict(result),
                    handle,
                    indent=2,
                )

        return result
