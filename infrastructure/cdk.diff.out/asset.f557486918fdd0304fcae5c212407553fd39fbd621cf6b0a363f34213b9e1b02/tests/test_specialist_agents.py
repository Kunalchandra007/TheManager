import unittest

from services.agents import SpecialistOrchestrator
from services.search import Citation


class FakeBedrock:
    def __init__(self) -> None:
        self.requests: list[dict] = []

    def converse(self, **kwargs: object) -> dict:
        self.requests.append(kwargs)
        prompt = kwargs["messages"][0]["content"][0]["text"]
        if "Choose one or more specialists" in prompt:
            return {"output": {"message": {"content": [{"text": '{"specialists":["schedule","political","reporting"],"rationale":"full analysis"}'}]}}}
        return {"output": {"message": {"content": [{"text": "analysis"}]}}}


class FakeSearch:
    def research(self, _: str) -> list[Citation]:
        return [Citation(title="Source", url="https://example.test", snippet="Evidence", published_date=None)]


class SpecialistAgentTests(unittest.TestCase):
    def test_specialists_return_citations_and_all_calls_use_guardrails(self) -> None:
        client = FakeBedrock()
        result = SpecialistOrchestrator("supervisor", "routine", "guardrail", FakeSearch(), client).run("assess risk", [{"equipment_id": 1}])
        self.assertEqual(result["route"], ["schedule", "political", "reporting"])
        self.assertEqual(result["citations"][0]["url"], "https://example.test")
        self.assertTrue(all(call["guardrailConfig"]["guardrailIdentifier"] == "guardrail" for call in client.requests))


if __name__ == "__main__":
    unittest.main()
