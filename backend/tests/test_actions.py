import unittest

from services.actions import ActionService


class Table:
    def __init__(self) -> None:
        self.items: dict[str, dict] = {}
    def put_item(self, Item: dict) -> None:
        self.items[Item["action_id"]] = Item
    def get_item(self, Key: dict) -> dict:
        return {"Item": self.items.get(Key["action_id"])} if Key["action_id"] in self.items else {}
    def update_item(self, Key: dict, **kwargs: object) -> None:
        self.items[Key["action_id"]]["status"] = "approved"


class ActionTests(unittest.TestCase):
    def test_proposal_needs_approval_before_dispatch(self) -> None:
        service = ActionService(Table())
        action = service.propose("supplier@example.com", "Expedite", "Please expedite.", [])
        self.assertEqual(action.status, "pending")
        self.assertEqual(service.approve(action.action_id, "reviewer")["status"], "approved")
