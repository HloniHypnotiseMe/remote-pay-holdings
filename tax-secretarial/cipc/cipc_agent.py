#!/usr/bin/env python3
"""
C6 CIPC Agent.

Annual-return and corporate-record readiness engine.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable, Optional


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

        return {
            "checks": checks,
            "filing_ready": ready,
            "status": (
                "READY_FOR_FILING_REVIEW"
                if ready
                else "REVIEW_REQUIRED"
            ),
        }

    def director_change_checklist(
        self,
    ) -> dict:

        return {
            "board_resolution_or_authorising_document": False,
            "identity_and_supporting_documents": False,
            "director_consent_or_required_support": False,
            "company_register_updated": False,
            "cipc_submission_completed": False,
            "proof_or_reference_captured": False,
            "status": "REVIEW_REQUIRED",
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
        }
