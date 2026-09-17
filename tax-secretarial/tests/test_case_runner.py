import unittest

from core.case_runner import AgentCall, run_case
from core.contracts import AgentResult, EvidenceItem


class FakeCIPC:
    def annual_return_review(self, company):
        return {
            "status": "READY",
            "entity": company,
            "summary": "Annual return review ready.",
            "evidence": [
                {
                    "evidence_id": "CIPC-001",
                    "source": "CIPC",
                    "claim": "Annual return review completed.",
                }
            ],
        }


class FakeSARS:
    def review(self, company, tax_year):
        return AgentResult(
            agent="SARSFilingAgent",
            status="REVIEW_REQUIRED",
            entity=company,
            summary="SARS review required.",
            missing_data=[f"tax_year:{tax_year}"],
            evidence=[
                EvidenceItem(
                    evidence_id="SARS-001",
                    source="SARS",
                    claim="SARS review requires confirmation.",
                )
            ],
        )


class TestCaseRunner(unittest.TestCase):

    def test_executes_real_agent_method_and_aggregates(self):
        result = run_case(
            "ABC Pty Ltd",
            [
                AgentCall(
                    agent="CIPCComplianceAgent",
                    method="annual_return_review",
                    args=("ABC Pty Ltd",),
                ),
                AgentCall(
                    agent="SARSFilingAgent",
                    method="review",
                    args=("ABC Pty Ltd", 2026),
                ),
            ],
            {
                "CIPCComplianceAgent": FakeCIPC(),
                "SARSFilingAgent": FakeSARS(),
            },
        )

        self.assertEqual(len(result.results), 2)
        self.assertTrue(result.review_required)
        self.assertEqual(result.missing_data, ["tax_year:2026"])
        self.assertEqual(len(result.evidence), 2)

    def test_kwargs_are_passed_to_agent(self):
        class Agent:
            def check(self, entity, regime=None):
                return {
                    "status": "READY",
                    "entity": entity,
                    "summary": regime,
                }

        result = run_case(
            "ABC Pty Ltd",
            [
                AgentCall(
                    agent="TaxDirector",
                    method="check",
                    kwargs={
                        "entity": "ABC Pty Ltd",
                        "regime": "SBC",
                    },
                )
            ],
            {"TaxDirector": Agent()},
        )

        self.assertTrue(result.ready)
        self.assertEqual(
            result.results[0].result.summary,
            "SBC",
        )

    def test_unknown_agent_fails_explicitly(self):
        with self.assertRaises(KeyError):
            run_case(
                "ABC Pty Ltd",
                [
                    AgentCall(
                        agent="UnknownAgent",
                        method="check",
                    )
                ],
                {},
            )

    def test_unknown_method_fails_explicitly(self):
        with self.assertRaises(AttributeError):
            run_case(
                "ABC Pty Ltd",
                [
                    AgentCall(
                        agent="CIPCComplianceAgent",
                        method="does_not_exist",
                    )
                ],
                {"CIPCComplianceAgent": FakeCIPC()},
            )


if __name__ == "__main__":
    unittest.main()
