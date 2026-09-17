#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(
    name: str,
    path: Path,
):
    spec = importlib.util.spec_from_file_location(
        name,
        path,
    )

    if spec is None or spec.loader is None:
        raise ImportError(
            f"Unable to create import spec for {path}"
        )

    module = importlib.util.module_from_spec(spec)

    if str(ROOT) not in sys.path:
        sys.path.insert(
            0,
            str(ROOT),
        )

    sys.modules[name] = module

    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(name, None)
        raise

    return module


tax_director = load_module(
    "c6_tax_director",
    ROOT / "director" / "tax_director.py",
)

sars_agent = load_module(
    "c6_sars_agent",
    ROOT / "sars" / "sars_filing_agent.py",
)

cipc_agent = load_module(
    "c6_cipc_agent",
    ROOT / "cipc" / "cipc_agent.py",
)

international = load_module(
    "c6_international",
    ROOT
    / "international"
    / "international_tax_analyst.py",
)

calendar_agent = load_module(
    "c6_calendar",
    ROOT
    / "calendar"
    / "compliance_calendar.py",
)


class TestTaxDirector(unittest.TestCase):

    def test_sbc_100k(self):
        self.assertAlmostEqual(
            tax_director.calculate_sbc_tax(
                100_000
            ),
            70.0,
        )

    def test_standard_cit(self):
        self.assertEqual(
            tax_director.calculate_cit(
                100_000
            ),
            27_000,
        )

    def test_turnover_tax(self):
        self.assertEqual(
            tax_director.calculate_turnover_tax(
                1_000_000
            ),
            4_500,
        )

    def test_missing_regime_requires_review(self):

        result = (
            tax_director.TaxDirector()
            .review_entity({
                "entity": "C6 Group",
                "taxable_income": 100_000,
            })
        )

        self.assertEqual(
            result.status,
            "REVIEW_REQUIRED",
        )

    def test_accounting_profit_not_taxable_income(self):

        result = (
            tax_director.TaxDirector()
            .review_entity({
                "entity": "C6 Group",
                "accounting_profit": 100_000,
                "taxable_income": 80_000,
                "tax_regime": "standard_cit",
            })
        )

        self.assertEqual(
            result.estimated_tax,
            21_600,
        )


class TestSARS(unittest.TestCase):

    def setUp(self):
        self.agent = (
            sars_agent.SARSFilingAgent()
        )

    def test_itr14(self):

        self.assertEqual(
            self.agent.itr14_due_date(
                date(2026, 2, 28)
            ),
            date(2027, 2, 28),
        )

    def test_first_provisional(self):

        result = (
            self.agent.provisional_dates(
                date(2026, 3, 1),
                date(2027, 2, 28),
            )
        )

        self.assertEqual(
            result["P1"],
            date(2026, 8, 31),
        )

    def test_second_provisional_weekend_adjustment(self):

        result = (
            self.agent.provisional_dates(
                date(2026, 3, 1),
                date(2027, 2, 28),
            )
        )

        self.assertEqual(
            result["P2"],
            date(2027, 2, 26),
        )

    def test_third_provisional(self):

        result = (
            self.agent.provisional_dates(
                date(2026, 3, 1),
                date(2027, 2, 28),
            )
        )

        self.assertEqual(
            result["P3"],
            date(2027, 9, 30),
        )

    def test_emp201(self):

        self.assertEqual(
            self.agent.emp201_due_date(
                date(2026, 8, 1)
            ),
            date(2026, 9, 7),
        )

    def test_emp201_weekend(self):

        self.assertEqual(
            self.agent.emp201_due_date(
                date(2026, 10, 1)
            ),
            date(2026, 11, 6),
        )

    def test_vat201(self):

        self.assertEqual(
            self.agent.vat201_due_date(
                date(2026, 8, 1),
                electronic=True,
            ),
            date(2026, 9, 30),
        )

    def test_company_schedule_contains_evidence(self):
        result = self.agent.prepare_company_schedule(
            date(2026, 3, 1),
            date(2027, 2, 28),
        )

        self.assertIn("evidence", result)
        self.assertGreaterEqual(len(result["evidence"]), 2)
        self.assertTrue(
            all(
                item["source"] == "SARSFilingAgent"
                for item in result["evidence"]
            )
        )
        self.assertTrue(
            all(
                item["status"] == "CALCULATED"
                for item in result["evidence"]
            )
        )

    def test_emp201_contains_evidence(self):
        result = self.agent.prepare_emp201(
            date(2026, 8, 1),
            True,
        )

        self.assertEqual(
            result["evidence"][0]["evidence_id"],
            "SARS-EMP201",
        )
        self.assertEqual(
            result["evidence"][0]["status"],
            "CALCULATED",
        )

    def test_vat201_contains_evidence(self):
        result = self.agent.prepare_vat201(
            date(2026, 8, 1),
            True,
        )

        self.assertEqual(
            result["evidence"][0]["evidence_id"],
            "SARS-VAT201",
        )
        self.assertEqual(
            result["evidence"][0]["status"],
            "CALCULATED",
        )

    def test_no_submission_claim(self):

        result = (
            self.agent.prepare_company_schedule(
                date(2026, 3, 1),
                date(2027, 2, 28),
            )
        )

        self.assertFalse(
            result["submission_claimed"]
        )


class TestCIPC(unittest.TestCase):

    def setUp(self):
        self.agent = (
            cipc_agent.CIPCComplianceAgent()
        )

    def test_30_business_days(self):

        self.assertEqual(
            self.agent.annual_return_due_date(
                date(2026, 7, 30)
            ),
            date(2026, 9, 10),
        )

    def test_fee(self):

        self.assertEqual(
            self.agent.annual_return_fee(
                500_000
            ),
            100,
        )

    def test_late_fee(self):

        self.assertEqual(
            self.agent.annual_return_fee(
                500_000,
                late=True,
            ),
            150,
        )

    def test_filing_gate(self):

        result = (
            self.agent
            .beneficial_ownership_check(
                True,
                True,
                True,
                True,
            )
        )

        self.assertTrue(
            result["filing_ready"]
        )

    def test_evidence_contract(self):
        result = self.agent.beneficial_ownership_check(
            True,
            True,
            True,
            True,
        )

        self.assertIn("evidence", result)
        self.assertEqual(len(result["evidence"]), 4)
        self.assertTrue(
            all(
                item["source"] == "CIPCComplianceAgent"
                for item in result["evidence"]
            )
        )

    def test_director_change_has_evidence(self):
        result = self.agent.director_change_checklist()

        self.assertIn("evidence", result)
        self.assertEqual(len(result["evidence"]), 1)
        self.assertEqual(
            result["evidence"][0]["evidence_id"],
            "CIPC-DIRECTOR-CHANGE",
        )
        self.assertEqual(
            result["status"],
            "REVIEW_REQUIRED",
        )

    def test_annual_return_review_has_evidence(self):
        result = self.agent.annual_return_review(
            date(2026, 7, 30),
            500_000,
            True,
            True,
            True,
            True,
        )

        self.assertIn("evidence", result)
        self.assertEqual(len(result["evidence"]), 2)
        self.assertFalse(result["filing_claimed"])

    def test_incomplete_filing_gate(self):

        result = (
            self.agent
            .beneficial_ownership_check(
                False,
                True,
                True,
                True,
            )
        )

        self.assertFalse(
            result["filing_ready"]
        )


class TestInternational(unittest.TestCase):

    def setUp(self):

        self.agent = (
            international.InternationalTaxAnalyst()
        )

    def test_country_alias(self):

        result = (
            self.agent.screen_country(
                "UK"
            )
        )

        self.assertEqual(
            result["country"],
            "United Kingdom",
        )

        self.assertTrue(
            result[
                "screened_as_dta_country"
            ]
        )

    def test_treaty_not_automatic(self):

        result = (
            self.agent.treaty_review(
                "UK",
                "royalties",
            )
        )

        self.assertFalse(
            result[
                "treaty_relief_granted"
            ]
        )

    def test_domestic_wht(self):

        result = (
            self.agent
            .domestic_withholding_screen(
                "royalties",
                100_000,
            )
        )

        self.assertEqual(
            result["domestic_amount"],
            15_000,
        )

    def test_pillar_two(self):

        result = (
            self.agent.pillar_two_screen(
                800_000_000
            )
        )

        self.assertTrue(
            result["threshold_met"]
        )


class TestCalendar(unittest.TestCase):

    def test_real_date_event(self):

        calendar = (
            calendar_agent.ComplianceCalendar()
        )

        calendar.add_cipc_annual_return(
            "C6 Group",
            date(2026, 9, 10),
        )

        events = (
            calendar.upcoming(
                date(2026, 9, 1),
                30,
            )
        )

        self.assertEqual(
            len(events),
            1,
        )

        self.assertIsInstance(
            events[0].due_date,
            date,
        )

    def test_not_applicable_hidden(self):

        calendar = (
            calendar_agent.ComplianceCalendar()
        )

        calendar.add_paia_reporting(
            "C6 Group",
            False,
        )

        events = (
            calendar.upcoming(
                date(2026, 1, 1),
                365,
            )
        )

        self.assertEqual(
            len(events),
            0,
        )


if __name__ == "__main__":
    unittest.main(
        verbosity=2
    )


class TestTaxDirectorSBCEligibility(unittest.TestCase):
    def test_sbc_requires_actual_eligibility_facts(self):
        result = tax_director.TaxDirector().evaluate_sbc_eligibility(
            gross_income=1_000_000,
            all_shareholders_natural_persons=None,
            personal_service_company=None,
            holding_company=None,
        )

        self.assertIsNone(result.eligible)
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn("all_shareholders_natural_persons", result.missing_data)

    def test_sbc_explicit_disqualifier_blocks(self):
        result = tax_director.TaxDirector().evaluate_sbc_eligibility(
            gross_income=1_000_000,
            all_shareholders_natural_persons=False,
            personal_service_company=False,
            holding_company=False,
        )

        self.assertFalse(result.eligible)
        self.assertEqual(result.status, "BLOCKED")

    def test_sbc_ready_when_all_facts_support_eligibility(self):
        result = tax_director.TaxDirector().evaluate_sbc_eligibility(
            gross_income=1_000_000,
            all_shareholders_natural_persons=True,
            personal_service_company=False,
            holding_company=False,
        )

        self.assertTrue(result.eligible)
        self.assertEqual(result.status, "READY")

    def test_sbc_review_does_not_calculate_tax_without_eligibility(self):
        result = tax_director.TaxDirector().review_entity(
            "Test Entity",
            tax_regime="sbc",
            taxable_income=500_000,
            gross_income=1_000_000,
            all_shareholders_natural_persons=None,
            personal_service_company=None,
            holding_company=None,
        )

        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIsNone(result.estimated_tax)


class TestTaxDirectorSBCEligibility(unittest.TestCase):

    def test_sbc_requires_actual_eligibility_facts(self):
        result = tax_director.TaxDirector().evaluate_sbc_eligibility(
            gross_income=1_000_000,
            all_shareholders_natural_persons=None,
            personal_service_company=None,
            holding_company=None,
        )

        self.assertIsNone(result.eligible)
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn(
            "all_shareholders_natural_persons",
            result.missing_data,
        )

    def test_sbc_explicit_disqualifier_blocks(self):
        result = tax_director.TaxDirector().evaluate_sbc_eligibility(
            gross_income=1_000_000,
            all_shareholders_natural_persons=False,
            personal_service_company=False,
            holding_company=False,
        )

        self.assertFalse(result.eligible)
        self.assertEqual(result.status, "BLOCKED")

    def test_sbc_ready_when_all_facts_support_eligibility(self):
        result = tax_director.TaxDirector().evaluate_sbc_eligibility(
            gross_income=1_000_000,
            all_shareholders_natural_persons=True,
            personal_service_company=False,
            holding_company=False,
        )

        self.assertTrue(result.eligible)
        self.assertEqual(result.status, "READY")

    def test_sbc_review_does_not_calculate_tax_without_eligibility(self):
        result = tax_director.TaxDirector().review_entity(
            "Test Entity",
            tax_regime="sbc",
            taxable_income=500_000,
            gross_income=1_000_000,
            all_shareholders_natural_persons=None,
            personal_service_company=None,
            holding_company=None,
        )

        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIsNone(result.estimated_tax)
