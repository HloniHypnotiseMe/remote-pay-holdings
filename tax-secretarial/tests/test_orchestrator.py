import unittest

from core.contracts import AgentResult, EvidenceItem
from core.orchestrator import orchestrate_results, run_agents


class TestOrchestrator(unittest.TestCase):

    def test_aggregates_normalized_results(self):
        result = orchestrate_results(
            "ABC Pty Ltd",
            [
                {
                    "agent": "CIPCComplianceAgent",
                    "status": "READY",
                    "entity": "ABC Pty Ltd",
                    "evidence": [
                        {
                            "evidence_id": "CIPC-001",
                            "source": "CIPC",
                            "claim": "Filing ready.",
                        }
                    ],
                },
                AgentResult(
                    agent="SARSFilingAgent",
                    status="READY",
                    entity="ABC Pty Ltd",
                ),
            ],
        )

        self.assertEqual(len(result.results), 2)
        self.assertTrue(result.ready)
        self.assertFalse(result.review_required)
        self.assertEqual(len(result.evidence), 1)

    def test_review_required_propagates(self):
        result = orchestrate_results(
            "ABC Pty Ltd",
            [
                {
                    "agent": "TaxDirector",
                    "status": "REVIEW_REQUIRED",
                    "entity": "ABC Pty Ltd",
                    "missing_data": ["tax_regime"],
                    "warnings": ["Human review required."],
                }
            ],
        )

        self.assertFalse(result.ready)
        self.assertTrue(result.review_required)
        self.assertEqual(result.missing_data, ["tax_regime"])
        self.assertEqual(result.warnings, ["Human review required."])

    def test_duplicate_missing_data_and_warnings_are_deduplicated(self):
        result = orchestrate_results(
            "ABC Pty Ltd",
            [
                {
                    "agent": "AgentA",
                    "status": "REVIEW_REQUIRED",
                    "entity": "ABC Pty Ltd",
                    "missing_data": ["tax_regime", "country"],
                    "warnings": ["Review"],
                },
                {
                    "agent": "AgentB",
                    "status": "REVIEW_REQUIRED",
                    "entity": "ABC Pty Ltd",
                    "missing_data": ["country", "tax_regime"],
                    "warnings": ["Review", "Check evidence"],
                },
            ],
        )

        self.assertEqual(
            result.missing_data,
            ["tax_regime", "country"],
        )
        self.assertEqual(
            result.warnings,
            ["Review", "Check evidence"],
        )

    def test_source_payloads_are_preserved(self):
        source = {
            "agent": "InternationalTaxAnalyst",
            "status": "READY",
            "entity": "ABC Pty Ltd",
            "country": "UK",
            "domain_fact": "preserve me",
        }

        result = orchestrate_results("ABC Pty Ltd", [source])

        self.assertIs(result.results[0].source, source)
        self.assertEqual(
            result.results[0].source["domain_fact"],
            "preserve me",
        )

    def test_to_dict_exposes_normalized_contract(self):
        result = orchestrate_results(
            "ABC Pty Ltd",
            [
                {
                    "agent": "SARSFilingAgent",
                    "status": "READY",
                    "entity": "ABC Pty Ltd",
                    "summary": "Ready.",
                }
            ],
        )

        payload = result.to_dict()

        self.assertEqual(payload["entity"], "ABC Pty Ltd")
        self.assertEqual(payload["status"], "READY")
        self.assertEqual(
            payload["results"][0]["agent"],
            "SARSFilingAgent",
        )

    def test_run_agents_uses_explicit_agent_names(self):
        def fake_sars(entity):
            return {
                "status": "READY",
                "entity": entity,
                "summary": "SARS ready.",
            }

        result = run_agents(
            "ABC Pty Ltd",
            {"SARSFilingAgent": fake_sars},
        )

        self.assertTrue(result.ready)
        self.assertEqual(
            result.results[0].result.agent,
            "SARSFilingAgent",
        )

    def test_empty_results_are_not_ready(self):
        result = orchestrate_results("ABC Pty Ltd", [])

        self.assertFalse(result.ready)
        self.assertFalse(result.review_required)
        self.assertEqual(result.to_dict()["status"], "NO_RESULTS")


if __name__ == "__main__":
    unittest.main()
