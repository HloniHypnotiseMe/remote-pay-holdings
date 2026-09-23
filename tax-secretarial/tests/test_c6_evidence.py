import os
import unittest

from core.c6_evidence import build_evidence_contract, publish_evidence
from core.contracts import EvidenceItem


class TestC6Evidence(unittest.TestCase):
    def setUp(self):
        self.evidence = EvidenceItem(
            evidence_id="SARS-001",
            source="SARS",
            claim="Return period identified.",
            status="VERIFIED",
            notes="Source record checked.",
        )

    def test_builds_canonical_contract(self):
        payload = build_evidence_contract(
            tenant_id="tenant-1",
            entity="ABC Pty Ltd",
            capability="sars_filing",
            evidence=self.evidence,
        )
        self.assertEqual(payload["product_id"], "tax_secretarial")
        self.assertEqual(payload["status"], "VERIFIED")
        self.assertEqual(payload["evidence"]["evidence_id"], "SARS-001")

    def test_missing_platform_configuration_is_gap(self):
        os.environ.pop("C6_EVIDENCE_API_URL", None)
        result = publish_evidence(
            tenant_id="tenant-1",
            entity="ABC Pty Ltd",
            capability="sars_filing",
            evidence=self.evidence,
        )
        self.assertFalse(result["published"])
        self.assertEqual(result["status"], "GAP")


if __name__ == "__main__":
    unittest.main()
