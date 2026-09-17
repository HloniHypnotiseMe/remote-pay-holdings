import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.adapter import adapt_result, adapt_result_with_source
from core.contracts import AgentResult, EvidenceItem


class TestAdapter(unittest.TestCase):

    def test_agent_result_passthrough(self):
        evidence = EvidenceItem(
            evidence_id="TEST-001",
            source="test",
            claim="Known fact",
            status="VERIFIED",
        )
        original = AgentResult(
            agent="TestAgent",
            status="READY",
            entity="ENTITY-1",
            summary="Ready",
            missing_data=["optional"],
            warnings=["test warning"],
            evidence=[evidence],
        )

        result = adapt_result(original)

        self.assertIs(result, original)

    def test_dict_result_normalizes(self):
        result = adapt_result(
            {
                "agent": "SARSFilingAgent",
                "status": "READY",
                "entity": "ABC Pty Ltd",
                "summary": "Filing ready.",
                "missing_data": [],
                "warnings": ["Review before submission."],
                "evidence": [
                    {
                        "evidence_id": "SARS-001",
                        "source": "SARS",
                        "claim": "Return period identified.",
                        "status": "CALCULATED",
                    }
                ],
            }
        )

        self.assertIsInstance(result, AgentResult)
        self.assertEqual(result.agent, "SARSFilingAgent")
        self.assertEqual(result.status, "READY")
        self.assertEqual(result.entity, "ABC Pty Ltd")
        self.assertEqual(result.warnings, ["Review before submission."])
        self.assertIsInstance(result.evidence[0], EvidenceItem)
        self.assertEqual(result.evidence[0].evidence_id, "SARS-001")

    def test_object_with_to_dict_normalizes(self):
        class LegacyResult:
            def to_dict(self):
                return {
                    "status": "REVIEW_REQUIRED",
                    "summary": "More facts required.",
                    "missing_data": ["tax_regime"],
                    "warnings": [],
                    "evidence": [
                        EvidenceItem(
                            evidence_id="TAX-001",
                            source="Tax Director",
                            claim="Tax regime is unknown.",
                        )
                    ],
                }

        result = adapt_result(
            LegacyResult(),
            agent="TaxDirector",
            entity="ABC Pty Ltd",
        )

        self.assertEqual(result.agent, "TaxDirector")
        self.assertEqual(result.entity, "ABC Pty Ltd")
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertEqual(result.missing_data, ["tax_regime"])
        self.assertEqual(result.evidence[0].evidence_id, "TAX-001")

    def test_evidence_dict_and_object_both_supported(self):
        result = adapt_result(
            {
                "agent": "CIPCComplianceAgent",
                "status": "REVIEW_REQUIRED",
                "entity": "ABC Pty Ltd",
                "evidence": [
                    EvidenceItem(
                        evidence_id="CIPC-001",
                        source="CIPC",
                        claim="Existing evidence.",
                    ),
                    {
                        "evidence_id": "CIPC-002",
                        "source": "CIPC",
                        "claim": "Dictionary evidence.",
                    },
                ],
            }
        )

        self.assertEqual(len(result.evidence), 2)
        self.assertTrue(
            all(isinstance(item, EvidenceItem) for item in result.evidence)
        )

    def test_source_is_preserved(self):
        source = {
            "agent": "InternationalTaxAnalyst",
            "status": "REVIEW_REQUIRED",
            "entity": "ABC Pty Ltd",
            "summary": "Review required.",
            "country": "UK",
            "custom_domain_field": "must survive",
            "evidence": [],
        }

        adapted = adapt_result_with_source(source)

        self.assertIs(adapted.source, source)
        self.assertEqual(
            adapted.source["custom_domain_field"],
            "must survive",
        )
        self.assertEqual(adapted.result.agent, "InternationalTaxAnalyst")

    def test_missing_agent_fails_explicitly(self):
        with self.assertRaises(ValueError):
            adapt_result(
                {
                    "status": "READY",
                    "entity": "ABC Pty Ltd",
                }
            )

    def test_missing_entity_fails_explicitly(self):
        with self.assertRaises(ValueError):
            adapt_result(
                {
                    "agent": "TestAgent",
                    "status": "READY",
                }
            )

    def test_invalid_evidence_fails_explicitly(self):
        with self.assertRaises(ValueError):
            adapt_result(
                {
                    "agent": "TestAgent",
                    "status": "READY",
                    "entity": "ABC Pty Ltd",
                    "evidence": [{"source": "test"}],
                }
            )


if __name__ == "__main__":
    unittest.main()
