#!/usr/bin/env python3
"""
C6 SARS Filing Agent.

Preparation and deadline engine only.
It does not claim to submit anything to SARS.
"""

from __future__ import annotations

import calendar as std_calendar
from datetime import date, timedelta
from typing import Iterable, Optional


def add_months(
    value: date,
    months: int,
) -> date:

    month_index = value.month - 1 + months

    year = value.year + (
        month_index // 12
    )

    month = (
        month_index % 12
    ) + 1

    day = min(
        value.day,
        std_calendar.monthrange(
            year,
            month,
        )[1],
    )

    return date(
        year,
        month,
        day,
    )


def last_day_of_month(
    value: date,
) -> date:

    return date(
        value.year,
        value.month,
        std_calendar.monthrange(
            value.year,
            value.month,
        )[1],
    )


def previous_business_day(
    value: date,
    holidays: Optional[
        Iterable[date]
    ] = None,
) -> date:

    holidays = set(
        holidays or []
    )

    while (
        value.weekday() >= 5
        or value in holidays
    ):
        value -= timedelta(
            days=1
        )

    return value


class SARSFilingAgent:

    def __init__(
        self,
        public_holidays: Optional[
            Iterable[date]
        ] = None,
    ):
        self.public_holidays = set(
            public_holidays or []
        )

    def provisional_dates(
        self,
        financial_year_start: date,
        financial_year_end: date,
    ) -> dict[str, date]:

        first_target = last_day_of_month(
            add_months(
                financial_year_start,
                5,
            )
        )

        second_target = (
            financial_year_end
        )

        if financial_year_end.month == 2:

            third_target = date(
                financial_year_end.year,
                9,
                30,
            )

        else:

            third_target = last_day_of_month(
                add_months(
                    financial_year_end,
                    6,
                )
            )

        return {
            "P1": previous_business_day(
                first_target,
                self.public_holidays,
            ),
            "P2": previous_business_day(
                second_target,
                self.public_holidays,
            ),
            "P3": previous_business_day(
                third_target,
                self.public_holidays,
            ),
        }

    def itr14_due_date(
        self,
        financial_year_end: date,
    ) -> date:

        return add_months(
            financial_year_end,
            12,
        )

    def emp201_due_date(
        self,
        payroll_month: date,
    ) -> date:

        following = add_months(
            date(
                payroll_month.year,
                payroll_month.month,
                1,
            ),
            1,
        )

        target = date(
            following.year,
            following.month,
            7,
        )

        return previous_business_day(
            target,
            self.public_holidays,
        )

    def vat201_due_date(
        self,
        vat_period_month: date,
        electronic: bool = True,
    ) -> date:

        following = add_months(
            date(
                vat_period_month.year,
                vat_period_month.month,
                1,
            ),
            1,
        )

        if electronic:

            target = last_day_of_month(
                following
            )

        else:

            target = date(
                following.year,
                following.month,
                25,
            )

        return previous_business_day(
            target,
            self.public_holidays,
        )

    def prepare_company_schedule(
        self,
        financial_year_start: date,
        financial_year_end: date,
    ) -> dict:

        provisional = (
            self.provisional_dates(
                financial_year_start,
                financial_year_end,
            )
        )

        return {
            "status": "PREPARATION_ONLY",
            "financial_year_start":
                financial_year_start.isoformat(),
            "financial_year_end":
                financial_year_end.isoformat(),
            "ITR14":
                self.itr14_due_date(
                    financial_year_end
                ).isoformat(),
            "P1":
                provisional["P1"].isoformat(),
            "P2":
                provisional["P2"].isoformat(),
            "P3":
                provisional["P3"].isoformat(),
            "submission_claimed": False,
        }

    def prepare_emp201(
        self,
        payroll_month: date,
        paye_registered: bool,
    ) -> dict:

        return {
            "obligation": "EMP201",
            "applicable": bool(
                paye_registered
            ),
            "due_date": (
                self.emp201_due_date(
                    payroll_month
                ).isoformat()
                if paye_registered
                else None
            ),
            "status": "PREPARATION_ONLY",
            "submission_claimed": False,
        }

    def prepare_vat201(
        self,
        vat_period_month: date,
        vat_registered: bool,
        electronic: bool = True,
    ) -> dict:

        return {
            "obligation": "VAT201",
            "applicable": bool(
                vat_registered
            ),
            "due_date": (
                self.vat201_due_date(
                    vat_period_month,
                    electronic,
                ).isoformat()
                if vat_registered
                else None
            ),
            "electronic": electronic,
            "status": "PREPARATION_ONLY",
            "submission_claimed": False,
        }
