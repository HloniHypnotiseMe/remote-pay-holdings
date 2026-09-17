#!/usr/bin/env python3
"""
C6 CIPC Agent.

Annual-return and corporate-record readiness engine.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable, Optional
from core.contracts import EvidenceItem


def add_business_days(
    start: date,
    business_days: int,
    holidays: Optional[
        Iterable[date]
    ] = None,
) -> date:

    holidays = set(
        holidays or []
    )

    current = start
    remaining = business_days

    while remaining > 0:

        current += timedelta(
            days=1
        )

        if (
            current.weekday() < 5
            and current not in holidays
        ):
            remaining -= 1

    return current


class CIPCComplianceAgent:
    agent_name = "cipc_compliance_agent"

    ANNUAL_RETURN_FEES = (
        (1_000_000, 100, 150),
        (10_000_000, 450, 600),
        (25_000_000, 2_000, 2_500),
        (float("inf"), 3_000, 4_000),
    )

    def __init__(
        self,
        public_holidays: Optional[
            Iterable[date]
        ] = None,
    ):
        self.public_holidays = set(
            public_holidays or []
        )

    def annual_return_due_date(
        self,
        incorporation_anniversary: date,
    ) -> date:

        return add_business_days(
            incorporation_anniversary,
            30,
            self.public_holidays,
        )

    def annual_return_fee(
        self,
        turnover_or_revenue: float,
        late: bool = False,
    ) -> int:

        amount = float(
            turnover_or_revenue
        )

        for (
            upper_limit,
            on_time,
            late_fee,
        ) in self.ANNUAL_RETURN_FEES:

            if amount < upper_limit:
                return (
                    late_fee
                    if late
                    else on_time
                )

        return 0

    def beneficial_ownership_check(
        self,
        beneficial_ownership_current: bool,
        latest_afs_or_fas_available: bool,
        security_or_beneficial_interest_records_ready: bool,
        compliance_checklist_complete: bool,
    ) -> dict:

        checks = {
            "beneficial_ownership_current":
                bool(
                    beneficial_ownership_current
                ),
            "latest_afs_or_fas_available":
                bool(
                    latest_afs_or_fas_available
                ),
            "security_or_beneficial_interest_records_ready":
                bool(
                    security_or_beneficial_interest_records_ready
                ),
            "cipc_compliance_checklist_complete":
                bool(
                    compliance_checklist_complete
                ),
        }

        ready = all(
            checks.values()
        )

        evidence = [
            EvidenceItem(
                evidence_id=f"CIPC-CHECK-{name.upper()}",
                source="CIPCComplianceAgent",
                claim=(
                    f"CIPC readiness check '{name}' "
                    f"supplied as {value}."
                ),
                status="SUPPLIED",
                notes=(
                    "Readiness evidence only; no CIPC filing "
                    "or submission performed."
                ),
            )
            for name, value in checks.items()
        ]

        return {
            "checks": checks,
            "filing_ready": ready,
            "status": (
                "READY_FOR_FILING_REVIEW"
                if ready
                else "REVIEW_REQUIRED"
            ),
            "evidence": [
                item.to_dict()
                for item in evidence
            ],
        }

    def director_change_checklist(
        self,
    ) -> dict:

        checklist = {
            "board_resolution_or_authorising_document": False,
            "identity_and_supporting_documents": False,
            "director_consent_or_required_support": False,
            "company_register_updated": False,
            "cipc_submission_completed": False,
            "proof_or_reference_captured": False,
        }

        evidence = EvidenceItem(
            evidence_id="CIPC-DIRECTOR-CHANGE",
            source="CIPCComplianceAgent",
            claim=(
                "Director-change checklist prepared with all "
                "required completion gates initially unverified."
            ),
            status="REVIEW_REQUIRED",
            notes=(
                "No CIPC submission is claimed and no filing "
                "completion is inferred."
            ),
        )

        return {
            **checklist,
            "status": "REVIEW_REQUIRED",
            "evidence": [
                evidence.to_dict()
            ],
        }

    def annual_return_review(
        self,
        incorporation_anniversary: date,
        turnover_or_revenue: float,
        beneficial_ownership_current: bool,
        latest_afs_or_fas_available: bool,
        security_or_beneficial_interest_records_ready: bool,
        compliance_checklist_complete: bool,
    ) -> dict:

        readiness = (
            self.beneficial_ownership_check(
                beneficial_ownership_current,
                latest_afs_or_fas_available,
                security_or_beneficial_interest_records_ready,
                compliance_checklist_complete,
            )
        )

        evidence = [
            EvidenceItem(
                evidence_id="CIPC-ANNUAL-RETURN-DUE-DATE",
                source="CIPCComplianceAgent",
                claim=(
                    "Annual return review due date calculated "
                    "from the incorporation anniversary."
                ),
                status="CALCULATED",
                notes=(
                    "Preparation only; no CIPC filing performed."
                ),
            ),
            EvidenceItem(
                evidence_id="CIPC-ANNUAL-RETURN-FEES",
                source="CIPCComplianceAgent",
                claim=(
                    "Estimated on-time and late annual-return "
                    "fees calculated from supplied turnover/revenue."
                ),
                status="CALCULATED",
                notes=(
                    "Fee estimate only; no payment or filing performed."
                ),
            ),
        ]

        return {
            "obligation": "CIPC Annual Return",
            "due_date":
                self.annual_return_due_date(
                    incorporation_anniversary
                ).isoformat(),
            "estimated_on_time_fee":
                self.annual_return_fee(
                    turnover_or_revenue
                ),
            "estimated_late_fee":
                self.annual_return_fee(
                    turnover_or_revenue,
                    late=True,
                ),
            "readiness": readiness,
            "filing_claimed": False,
            "evidence": [
                item.to_dict()
                for item in evidence
            ],
        }
