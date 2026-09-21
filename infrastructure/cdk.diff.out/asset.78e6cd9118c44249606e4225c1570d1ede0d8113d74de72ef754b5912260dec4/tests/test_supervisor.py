import unittest

from services.supervisor import BedrockSupervisor


class FakeBedrock:
    def __init__(self) -> None:
        self.request: dict[str, object] = {}

    def converse(self, **kwargs: object) -> dict:
        self.request = kwargs
        return {"output": {"message": {"content": [{"text": '{"specialists":["schedule","political","reporting"],"rationale":"needs full analysis"}'}]}}}


class SupervisorTests(unittest.TestCase):
    def test_structured_supervisor_route_is_validated(self) -> None:
        client = FakeBedrock()
        decision = BedrockSupervisor("test-model", client, "guardrail-id").decide("give me a complete risk report")
        self.assertEqual(decision.specialists, ["schedule", "political", "reporting"])
        self.assertEqual(client.request["guardrailConfig"], {"guardrailIdentifier": "guardrail-id", "guardrailVersion": "DRAFT", "trace": "enabled"})


if __name__ == "__main__":
    unittest.main()
