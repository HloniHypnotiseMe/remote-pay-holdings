#!/usr/bin/env python3
"""
C6 Holdings Tax Configuration.

Company-specific facts must be explicitly supplied.
Missing facts must produce REVIEW_REQUIRED rather than guesses.
"""

from dataclasses import dataclass, field
from typing import Optional


SARS_TAX_YEAR = "2026/27"

STANDARD_CIT_RATE = 0.27

SBC_GROSS_INCOME_LIMIT = 20_000_000

SBC_TAXABLE_INCOME_BRACKETS = (
    (99_000, 0.00, 0),
    (365_000, 0.07, 0),
    (550_000, 0.21, 18_620),
    (float("inf"), 0.27, 57_470),
)

TURNOVER_TAX_THRESHOLD = 2_300_000

TURNOVER_TAX_BRACKETS = (
    (600_000, 0.00, 0),
    (950_000, 0.01, 0),
    (1_400_000, 0.02, 3_500),
    (2_300_000, 0.03, 12_500),
)

VAT_COMPULSORY_THRESHOLD = 2_300_000
VAT_VOLUNTARY_THRESHOLD = 120_000

DOMESTIC_WITHHOLDING_TAX = {
    "dividends": 0.20,
    "royalties": 0.15,
    "interest": 0.15,
}

PILLAR_TWO_REVENUE_THRESHOLD_EUR = 750_000_000


COUNTRY_ALIASES = {
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "great britain": "United Kingdom",
    "britain": "United Kingdom",
    "usa": "United States",
    "u.s.a.": "United States",
    "us": "United States",
    "uae": "United Arab Emirates",
    "u.a.e.": "United Arab Emirates",
    "swaziland": "Eswatini",
}


# Screening list only.
# Presence here does NOT automatically grant treaty relief.
DTA_COUNTRIES = {
    "Algeria",
    "Australia",
    "Austria",
    "Belgium",
    "Botswana",
    "Brazil",
    "Canada",
    "Chile",
    "China",
    "Croatia",
    "Cyprus",
    "Czech Republic",
    "Denmark",
    "Egypt",
    "Eswatini",
    "Ethiopia",
    "Finland",
    "France",
    "Germany",
    "Ghana",
    "Greece",
    "Hungary",
    "India",
    "Indonesia",
    "Iran",
    "Ireland",
    "Israel",
    "Italy",
    "Japan",
    "Kenya",
    "Korea",
    "Kuwait",
    "Lesotho",
    "Luxembourg",
    "Malawi",
    "Malaysia",
    "Malta",
    "Mauritius",
    "Mexico",
    "Mozambique",
    "Namibia",
    "Netherlands",
    "New Zealand",
    "Nigeria",
    "Norway",
    "Oman",
    "Pakistan",
    "Poland",
    "Portugal",
    "Qatar",
    "Romania",
    "Rwanda",
    "Saudi Arabia",
    "Seychelles",
    "Singapore",
    "Slovakia",
    "Spain",
    "Sri Lanka",
    "Sweden",
    "Switzerland",
    "Taiwan",
    "Thailand",
    "Tunisia",
    "Turkey",
    "Uganda",
    "Ukraine",
    "United Arab Emirates",
    "United Kingdom",
    "United States",
    "Zambia",
    "Zimbabwe",
}


@dataclass
class EntityConfig:
    name: str
    tax_number: Optional[str] = None
    financial_year_end: Optional[str] = None
    vat_registered: Optional[bool] = None
    paye_registered: Optional[bool] = None
    turnover_tax_registered: Optional[bool] = None
    sbc_eligible: Optional[bool] = None
    gross_income: Optional[float] = None
    cipc_incorporation_anniversary: Optional[str] = None
    beneficial_ownership_current: Optional[bool] = None
    latest_afs_or_fas_available: Optional[bool] = None
    paia_applicable: Optional[bool] = None
    public_holidays: list[str] = field(default_factory=list)


ENTITY_CONFIG = {
    "C6 Group": EntityConfig(name="C6 Group"),
    "RemotePay": EntityConfig(name="RemotePay"),
    "Ubernie": EntityConfig(name="Ubernie"),
}


def normalise_country(country: str) -> str:
    value = " ".join(country.strip().split())
    return COUNTRY_ALIASES.get(value.lower(), value)


def dta_screen(country: str) -> dict:
    normalized = normalise_country(country)

    return {
        "country": normalized,
        "screened_as_dta_country": normalized in DTA_COUNTRIES,
        "treaty_relief_assumed": False,
        "treaty_article_required": True,
        "beneficial_owner_review_required": True,
        "entitlement_review_required": True,
    }
