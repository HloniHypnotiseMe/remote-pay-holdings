#!/usr/bin/env python3
"""
C6 International Tax Analyst.

Treaty membership is never treated as automatic treaty relief.
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.tax_config import (
    DOMESTIC_WITHHOLDING_TAX,
    PILLAR_TWO_REVENUE_THRESHOLD_EUR,
    dta_screen,
    normalise_country,
)


class InternationalTaxAnalyst:

    def screen_country(
        self,
        country: str,
    ) -> dict:

        return dta_screen(country)

    def domestic_withholding_screen(
        self,
        payment_type: str,
        amount: float,
    ) -> dict:

        key = payment_type.strip().lower()

        rate = DOMESTIC_WITHHOLDING_TAX.get(
            key
        )

        if rate is None:

            return {
                "payment_type": key,
                "amount": float(amount),
                "domestic_rate": None,
                "status": "REVIEW_REQUIRED",
                "reason":
                    "Payment type is not in configured domestic WHT screen.",
            }

        return {
            "payment_type": key,
            "amount": float(amount),
            "domestic_rate": rate,
            "domestic_amount":
                round(
                    float(amount) * rate,
                    2,
                ),
            "status": "REVIEW_REQUIRED",
            "reason":
                "Domestic starting point identified; treaty exemption "
                "or reduced rate must be separately established.",
        }

    def treaty_review(
        self,
        country: str,
        payment_type: str,
        treaty_article: str | None = None,
        beneficial_owner_confirmed: bool | None = None,
        treaty_entitlement_confirmed: bool | None = None,
    ) -> dict:

        screen = self.screen_country(
            country
        )

        issues = []

        if not screen[
            "screened_as_dta_country"
        ]:
            issues.append(
                "DTA coverage not found in configured screening list."
            )

        if not treaty_article:
            issues.append(
                "Applicable treaty article not supplied."
            )

        if beneficial_owner_confirmed is not True:
            issues.append(
                "Beneficial ownership not confirmed."
            )

        if treaty_entitlement_confirmed is not True:
            issues.append(
                "Treaty entitlement not confirmed."
            )

        return {
            "country":
                normalise_country(country),
            "payment_type":
                payment_type,
            "dta_screen":
                screen,
            "treaty_relief_granted":
                False,
            "issues":
                issues,
            "status": (
                "READY_FOR_TAX_SPECIALIST_REVIEW"
                if not issues
                else "REVIEW_REQUIRED"
            ),
        }

    def permanent_establishment_screen(
        self,
        facts: dict[str, Any],
    ) -> dict:

        indicators = {
            "fixed_place_of_business":
                bool(
                    facts.get(
                        "fixed_place_of_business"
                    )
                ),
            "dependent_agent":
                bool(
                    facts.get(
                        "dependent_agent"
                    )
                ),
            "people_concluding_contracts":
                bool(
                    facts.get(
                        "people_concluding_contracts"
                    )
                ),
            "substantial_continuous_local_activity":
                bool(
                    facts.get(
                        "substantial_continuous_local_activity"
                    )
                ),
        }

        potential = any(
            indicators.values()
        )

        return {
            "indicators":
                indicators,
            "potential_pe":
                potential,
            "status": (
                "REVIEW_REQUIRED"
                if potential
                else "NO_INDICATOR_REPORTED"
            ),
        }

    def compliance_checklist(
        self,
        annual_group_revenue_eur:
            float | None = None,
    ) -> dict:

        pillar_two = (
            annual_group_revenue_eur
            is not None
            and float(
                annual_group_revenue_eur
            )
            >= PILLAR_TWO_REVENUE_THRESHOLD_EUR
        )

        return {
            "residence_and_source": False,
            "dta_article_and_rate": False,
            "beneficial_owner_and_treaty_entitlement": False,
            "permanent_establishment": False,
            "transfer_pricing": False,
            "foreign_tax_credit": False,
            "controlled_foreign_company": False,
            "exchange_control_sarb": False,
            "crs_aeoi": False,
            "fatca_if_applicable": False,
            "carf_if_applicable": False,
            "pillar_two_scope_review":
                pillar_two,
            "cbcr_scope_review": False,
            "foreign_entity_registration_and_substance": False,
            "status": "REVIEW_REQUIRED",
        }

    def pillar_two_screen(
        self,
        annual_group_revenue_eur: float,
    ) -> dict:

        revenue = float(
            annual_group_revenue_eur
        )

        threshold_met = (
            revenue
            >= PILLAR_TWO_REVENUE_THRESHOLD_EUR
        )

        return {
            "annual_group_revenue_eur":
                revenue,
            "threshold_eur":
                PILLAR_TWO_REVENUE_THRESHOLD_EUR,
            "threshold_met":
                threshold_met,
            "conclusion": (
                "SCOPE_REVIEW_REQUIRED"
                if threshold_met
                else "THRESHOLD_NOT_MET_ON_SUPPLIED_REVENUE"
            ),
        }
