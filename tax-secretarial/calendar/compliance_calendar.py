#!/usr/bin/env python3
"""
C6 Compliance Calendar.

Events use real datetime.date objects and explicit applicability.
Calendar events retain evidence provenance from the domain agent that
calculated the obligation where available.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Optional

from core.contracts import EvidenceItem


@dataclass
class ComplianceEvent:
    entity: str
    authority: str
    obligation: str
    due_date: date
    applicable: bool
    owner: str
    status: str = "OPEN"
    evidence: Optional[str] = None
    notes: str = ""

    def evidence_item(self) -> EvidenceItem:
        return EvidenceItem(
            evidence_id=(
                self.evidence
                or (
                    "CALENDAR-"
                    f"{self.authority.upper()}-"
                    f"{self.obligation.upper().replace(' ', '-')}"
                )
            ),
            source="ComplianceCalendar",
            claim=(
                f"{self.authority} {self.obligation} "
                f"calendar event recorded for {self.entity}."
            ),
            status=self.status,
            notes=self.notes,
        )


class ComplianceCalendar:

    def __init__(self):
        self.events: list[ComplianceEvent] = []

    def add_event(
        self,
        event: ComplianceEvent,
    ) -> None:
        self.events.append(event)

    def _add_domain_event(
        self,
        entity: str,
        authority: str,
        obligation: str,
        due_date: date,
        owner: str,
        evidence: EvidenceItem | None = None,
        applicable: bool = True,
        status: str = "OPEN",
        notes: str = "",
    ) -> None:
        evidence_id = (
            evidence.evidence_id
            if evidence is not None
            else None
        )

        self.add_event(
            ComplianceEvent(
                entity=entity,
                authority=authority,
                obligation=obligation,
                due_date=due_date,
                applicable=applicable,
                owner=owner,
                status=status,
                evidence=evidence_id,
                notes=(
                    evidence.notes
                    if evidence is not None
                    else notes
                ),
            )
        )

    def add_sars_company(
        self,
        entity: str,
        financial_year_end: date,
        financial_year_start: date,
        owner: str = "Tax Director",
    ) -> None:
        import importlib.util

        path = (
            Path(__file__).resolve().parents[1]
            / "sars"
            / "sars_filing_agent.py"
        )

        spec = importlib.util.spec_from_file_location(
            "c6_sars_calendar_agent",
            path,
        )

        if spec is None or spec.loader is None:
            raise ImportError(
                "Unable to load SARS filing agent."
            )

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        agent = module.SARSFilingAgent()

        schedule = agent.prepare_company_schedule(
            financial_year_start,
            financial_year_end,
        )

        evidence_by_id = {
            item["evidence_id"]: item
            for item in schedule.get("evidence", [])
        }

        obligation_evidence = {
            "ITR14": evidence_by_id.get(
                "SARS-ITR14-DUE-DATE"
            ),
            "P1": evidence_by_id.get(
                "SARS-PROVISIONAL-DATES"
            ),
            "P2": evidence_by_id.get(
                "SARS-PROVISIONAL-DATES"
            ),
            "P3": evidence_by_id.get(
                "SARS-PROVISIONAL-DATES"
            ),
        }

        for obligation in (
            "ITR14",
            "P1",
            "P2",
            "P3",
        ):
            supplied_evidence = obligation_evidence.get(
                obligation
            )

            evidence_item = (
                EvidenceItem(**supplied_evidence)
                if supplied_evidence is not None
                else None
            )

            self._add_domain_event(
                entity=entity,
                authority="SARS",
                obligation=obligation,
                due_date=date.fromisoformat(
                    schedule[obligation]
                ),
                owner=owner,
                evidence=evidence_item,
                notes=(
                    "Preparation/review event; "
                    "submission not claimed."
                ),
            )

    def add_emp201(
        self,
        entity: str,
        payroll_month: date,
        due_date: date,
        owner: str = "Payroll / Tax",
    ) -> None:
        self._add_domain_event(
            entity=entity,
            authority="SARS",
            obligation="EMP201",
            due_date=due_date,
            owner=owner,
            evidence=EvidenceItem(
                evidence_id="CALENDAR-SARS-EMP201",
                source="ComplianceCalendar",
                claim=(
                    "EMP201 due date recorded from the "
                    "supplied payroll period."
                ),
                status="CALCULATED",
                notes=(
                    "Calendar event only; submission not claimed. "
                    f"Payroll period: {payroll_month.isoformat()}"
                ),
            ),
        )

    def add_vat201(
        self,
        entity: str,
        vat_period: date,
        due_date: date,
        owner: str = "Finance / Tax",
    ) -> None:
        self._add_domain_event(
            entity=entity,
            authority="SARS",
            obligation="VAT201",
            due_date=due_date,
            owner=owner,
            evidence=EvidenceItem(
                evidence_id="CALENDAR-SARS-VAT201",
                source="ComplianceCalendar",
                claim=(
                    "VAT201 due date recorded from the "
                    "supplied VAT period."
                ),
                status="CALCULATED",
                notes=(
                    "Calendar event only; submission not claimed. "
                    f"VAT period: {vat_period.isoformat()}"
                ),
            ),
        )

    def add_cipc_annual_return(
        self,
        entity: str,
        due_date: date,
        owner: str = "Company Secretary / Tax Director",
    ) -> None:
        self._add_domain_event(
            entity=entity,
            authority="CIPC",
            obligation="Annual Return",
            due_date=due_date,
            owner=owner,
            evidence=EvidenceItem(
                evidence_id="CALENDAR-CIPC-ANNUAL-RETURN",
                source="ComplianceCalendar",
                claim=(
                    "CIPC Annual Return due date recorded "
                    "in the compliance calendar."
                ),
                status="CALCULATED",
                notes=(
                    "BO and required financial/compliance "
                    "evidence must be current before filing."
                ),
            ),
        )

    def add_paia_reporting(
        self,
        entity: str,
        applicable: bool,
        owner: str = "Information Officer",
    ) -> None:
        self._add_domain_event(
            entity=entity,
            authority="Information Regulator",
            obligation="PAIA Annual Reporting",
            due_date=date(2026, 6, 30),
            applicable=applicable,
            owner=owner,
            evidence=EvidenceItem(
                evidence_id="CALENDAR-PAIA-ANNUAL-REPORTING",
                source="ComplianceCalendar",
                claim=(
                    "PAIA annual reporting calendar entry "
                    "recorded with explicit applicability."
                ),
                status=(
                    "REVIEW_REQUIRED"
                    if applicable
                    else "NOT_APPLICABLE"
                ),
                notes=(
                    "Applicability must be confirmed; "
                    "this obligation is not assumed universally."
                ),
            ),
        )

    def add_director_change_review(
        self,
        entity: str,
        review_date: date,
        owner: str = "Company Secretary",
    ) -> None:
        self._add_domain_event(
            entity=entity,
            authority="CIPC",
            obligation="Director Change Compliance Review",
            due_date=review_date,
            owner=owner,
            evidence=EvidenceItem(
                evidence_id="CALENDAR-CIPC-DIRECTOR-CHANGE",
                source="ComplianceCalendar",
                claim=(
                    "Director change compliance review "
                    "has been scheduled."
                ),
                status="REVIEW_REQUIRED",
                notes=(
                    "Review resolutions, identity documents, "
                    "registers and proof."
                ),
            ),
        )

    def upcoming(
        self,
        from_date: date,
        days: int = 30,
        include_not_applicable: bool = False,
    ) -> list[ComplianceEvent]:
        end_date = from_date + timedelta(days=days)

        results = [
            event
            for event in self.events
            if (
                from_date
                <= event.due_date
                <= end_date
            )
            and (
                include_not_applicable
                or event.applicable
            )
        ]

        return sorted(
            results,
            key=lambda event: event.due_date,
        )

    def overdue(
        self,
        as_of: date,
        include_not_applicable: bool = False,
    ) -> list[ComplianceEvent]:
        results = [
            event
            for event in self.events
            if event.due_date < as_of
            and (
                include_not_applicable
                or event.applicable
            )
            and event.status not in {
                "COMPLETED",
                "CLOSED",
                "NOT_APPLICABLE",
            }
        ]

        return sorted(
            results,
            key=lambda event: event.due_date,
        )

    def due_soon(
        self,
        as_of: date,
        days: int = 30,
        include_not_applicable: bool = False,
    ) -> list[ComplianceEvent]:
        return self.upcoming(
            as_of,
            days,
            include_not_applicable,
        )

    def save(
        self,
        path: str | Path,
    ) -> None:
        output = Path(path)
        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload: list[dict[str, Any]] = []

        for event in self.events:
            item = asdict(event)
            item["due_date"] = event.due_date.isoformat()
            payload.append(item)

        with output.open(
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(
                payload,
                handle,
                indent=2,
            )
