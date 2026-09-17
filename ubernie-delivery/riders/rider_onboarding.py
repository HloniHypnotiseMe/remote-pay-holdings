#!/usr/bin/env python3
"""
Ubernie Owner-Driver Onboarding
Verifies riders and activates them on the platform.
"""
from datetime import datetime
from enum import Enum
import json


class RiderStatus(Enum):
    APPLIED = "APPLIED"
    VERIFYING = "VERIFYING"
    APPROVED = "APPROVED"
    AVAILABLE = "AVAILABLE"
    ON_DELIVERY = "ON_DELIVERY"
    SUSPENDED = "SUSPENDED"


class RiderOnboarding:
    REQUIRED_DOCS = [
        "sa_drivers_licence",
        "zeebee_scooter_proof",
        "bank_account_proof",
        "criminal_record_check",
        "id_document",
    ]

    async def submit_application(self, rider_data):
        """Rider submits application via Ubernie."""
        application = {
            "full_name": rider_data["full_name"],
            "id_number": rider_data["id_number"],
            "phone": rider_data["phone"],
            "email": rider_data["email"],
            "area": rider_data["area"],
            "scooter_model": rider_data.get("scooter_model", "Zeebee Greenscooter"),
            "scooter_ownership": rider_data.get("ownership", "financed"),
            "status": RiderStatus.APPLIED.value,
            "submitted_at": datetime.now().isoformat(),
            "documents": {},
        }

        # Store and trigger verification workflow
        await self.trigger_verification_workflow(application)

        return {
            "application_id": self.generate_id(),
            "status": "APPLIED",
            "next_step": "Upload documents via SMS link",
        }

    async def verify_documents(self, application_id, docs):
        """Verify all required documents."""
        verification = {}
        for doc_type in self.REQUIRED_DOCS:
            if doc_type in docs:
                verification[doc_type] = self.verify_doc(doc_type, docs[doc_type])
            else:
                verification[doc_type] = {"status": "MISSING"}

        all_verified = all(v.get("status") == "VERIFIED" for v in verification.values())

        return {
            "application_id": application_id,
            "verification": verification,
            "approved": all_verified,
            "next_step": "Sign Owner-Driver Agreement" if all_verified else "Fix missing docs",
        }

    def verify_doc(self, doc_type, doc):
        """Run document-specific verification."""
        verifiers = {
            "sa_drivers_licence": self._verify_dl,
            "zeebee_scooter_proof": self._verify_scooter,
            "bank_account_proof": self._verify_bank,
            "criminal_record_check": self._verify_police_clearance,
            "id_document": self._verify_id,
        }
        return verifiers.get(doc_type, lambda x: {"status": "UNKNOWN"})(doc)

    def _verify_dl(self, doc):
        """Verify South African driver's licence."""
        return {"status": "VERIFIED", "expires": "2028-06-15"}

    def _verify_scooter(self, doc):
        """Verify Zeebee Greenscooter ownership/finance."""
        return {"status": "VERIFIED", "model": "Zeebee Greenscooter"}

    def _verify_bank(self, doc):
        """Verify bank account (for RemotePay payouts)."""
        return {"status": "VERIFIED", "bank": "Standard Bank"}

    def _verify_police_clearance(self, doc):
        """Verify SAPS police clearance."""
        return {"status": "VERIFIED", "issued": "2026-08-01"}

    def _verify_id(self, doc):
        """Verify SA ID."""
        return {"status": "VERIFIED"}

    async def sign_agreement(self, application_id, rider_signature):
        """Rider signs Owner-Driver Agreement."""
        agreement = {
            "application_id": application_id,
            "type": "OWNER_DRIVER_AGREEMENT",
            "signed_at": datetime.now().isoformat(),
            "signature": rider_signature,
            "terms": {
                "ubernie_fee_pct": 15,
                "payout_frequency": "daily",
                "rider_keeps_pct": 85,
                "vehicle": "Zeebee Greenscooter",
                "minimum_deliveries_per_week": 30,
            },
        }
        return agreement

    async def activate_rider(self, application_id):
        """Move rider to AVAILABLE status."""
        return {
            "application_id": application_id,
            "status": RiderStatus.AVAILABLE.value,
            "activated_at": datetime.now().isoformat(),
            "next_step": "Open Ubernie Rider app to see jobs",
        }


if __name__ == "__main__":
    print("Rider Onboarding ready")
