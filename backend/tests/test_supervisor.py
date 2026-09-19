import unittest

from services.supervisor import BedrockSupervisor


class FakeBedrock:
    def converse(self, **_: object) -> dict:
        return {"output": {"message": {"content": [{"text": '{"specialists":["schedule","political","reporting"],"rationale":"needs full analysis"}'}]}}}


class SupervisorTests(unittest.TestCase):
    def test_structured_supervisor_route_is_validated(self) -> None:
        decision = BedrockSupervisor("test-model", FakeBedrock()).decide("give me a complete risk report")
        self.assertEqual(decision.specialists, ["schedule", "political", "reporting"])


if __name__ == "__main__":
    unittest.main()
