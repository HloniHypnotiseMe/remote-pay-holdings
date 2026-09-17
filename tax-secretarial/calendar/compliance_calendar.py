#!/usr/bin/env python3
"""
C6 Compliance Calendar.

Events use real datetime.date objects and explicit applicability.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Optional


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


class ComplianceCalendar:

    def __init__(self):
        self.events: list[
            ComplianceEvent
        ] = []

    def add_event(
        self,
        event: ComplianceEvent,
    ) -> None:

        self.events.append(
            event
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

        spec = (
            importlib.util.spec_from_file_location(
                "c6_sars_calendar_agent",
                path,
            )
        )

        module = (
            importlib.util.module_from_spec(
                spec
            )
        )

        assert spec.loader is not None

        spec.loader.exec_module(
            module
        )

        agent = (
            module.SARSFilingAgent()
        )

        schedule = (
            agent.prepare_company_schedule(
                financial_year_start,
                financial_year_end,
            )
        )

        for obligation in (
            "ITR14",
            "P1",
            "P2",
            "P3",
        ):

            self.add_event(
                ComplianceEvent(
                    entity=entity,
                    authority="SARS",
                    obligation=obligation,
                    due_date=date.fromisoformat(
                        schedule[obligation]
                    ),
                    applicable=True,
                    owner=owner,
                    notes=(
                        "Preparation/review event; "
                        "submission not claimed."
                    ),
                )
            )

    def add_emp201(
        self,
        entity: str,
        payroll_month: date,
        due_date: date,
        owner: str = "Payroll / Tax",
    ) -> None:

        self.add_event(
            ComplianceEvent(
                entity=entity,
                authority="SARS",
                obligation="EMP201",
                due_date=due_date,
                applicable=True,
                owner=owner,
                notes=(
                    "Payroll period: "
                    f"{payroll_month.isoformat()}"
                ),
            )
        )

    def add_vat201(
        self,
        entity: str,
        vat_period: date,
        due_date: date,
        owner: str = "Finance / Tax",
    ) -> None:

        self.add_event(
            ComplianceEvent(
                entity=entity,
                authority="SARS",
                obligation="VAT201",
                due_date=due_date,
                applicable=True,
                owner=owner,
                notes=(
                    "VAT period: "
                    f"{vat_period.isoformat()}"
                ),
            )
        )

    def add_cipc_annual_return(
        self,
        entity: str,
        due_date: date,
        owner: str = "Company Secretary / Tax Director",
    ) -> None:

        self.add_event(
            ComplianceEvent(
                entity=entity,
                authority="CIPC",
                obligation="Annual Return",
                due_date=due_date,
                applicable=True,
                owner=owner,
                notes=(
                    "BO and required financial/compliance "
                    "evidence must be current before filing."
                ),
            )
        )

    def add_paia_reporting(
        self,
        entity: str,
        applicable: bool,
        owner: str = "Information Officer",
    ) -> None:

        self.add_event(
            ComplianceEvent(
                entity=entity,
                authority="Information Regulator",
                obligation="PAIA Annual Reporting",
                due_date=date(
                    2026,
                    6,
                    30,
                ),
                applicable=applicable,
                owner=owner,
                notes=(
                    "Applicability must be confirmed; "
                    "this obligation is not assumed universally."
                ),
            )
        )

    def add_director_change_review(
        self,
        entity: str,
        review_date: date,
        owner: str = "Company Secretary",
    ) -> None:

        self.add_event(
            ComplianceEvent(
                entity=entity,
                authority="CIPC",
                obligation="Director Change Compliance Review",
                due_date=review_date,
                applicable=True,
                owner=owner,
                notes=(
                    "Review resolutions, identity documents, "
                    "registers and proof."
                ),
            )
        )

    def upcoming(
        self,
        from_date: date,
        days: int = 30,
        include_not_applicable: bool = False,
    ) -> list[ComplianceEvent]:

        end_date = (
            from_date
            + timedelta(days=days)
        )

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
            key=lambda event:
                event.due_date,
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

        payload = []

        for event in self.events:

            item = asdict(
                event
            )

            item[
                "due_date"
            ] = event.due_date.isoformat()

            payload.append(
                item
            )

        with output.open(
            "w",
            encoding="utf-8",
        ) as handle:

            json.dump(
                payload,
                handle,
                indent=2,
            )
