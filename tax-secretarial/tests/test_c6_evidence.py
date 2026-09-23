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


    def test_publisher_targets_persistent_endpoint(self):
        os.environ["C6_EVIDENCE_API_URL"] = "https://core.example"
        captured = {}

        class FakeResponse:
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                return False
            def read(self):
                return b'{"id":"evidence-001","status":"VERIFIED"}'

        def fake_urlopen(request, timeout=5):
            captured["url"] = request.full_url
            return FakeResponse()

        with patch("core.c6_evidence.urlopen", fake_urlopen):
            result = publish_evidence(
                tenant_id="tenant-1",
                entity="ABC Pty Ltd",
                capability="sars_filing",
                evidence=self.evidence,
            )

        self.assertTrue(result["published"])
        self.assertEqual(result["evidence_id"], "evidence-001")
        self.assertEqual(captured["url"], "https://core.example/api/v1/evidence")
        os.environ.pop("C6_EVIDENCE_API_URL", None)
