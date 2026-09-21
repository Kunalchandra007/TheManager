"""Human-gated action workflow. This module never sends an email on proposal."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class PendingAction:
    action_id: str
    status: str
    draft_email: str
    evidence: list[dict[str, str]]
    created_at: str


class ActionService:
    def __init__(self, table: Any, ses_client: Any = None) -> None:
        self._table = table
        self._ses = ses_client

    def propose(self, supplier_email: str, subject: str, body: str, evidence: list[dict[str, str]]) -> PendingAction:
        action = PendingAction(str(uuid4()), "pending", f"To: {supplier_email}\nSubject: {subject}\n\n{body}", evidence, datetime.now(UTC).isoformat())
        self._table.put_item(Item=asdict(action))
        return action

    def approve(self, action_id: str, approved_by: str) -> dict[str, Any]:
        item = self._table.get_item(Key={"action_id": action_id}).get("Item")
        if not item or item["status"] != "pending":
            raise ValueError("Pending action not found")
        self._table.update_item(
            Key={"action_id": action_id},
            UpdateExpression="SET #status = :status, approved_by = :approved_by, approved_at = :approved_at",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": "approved", ":approved_by": approved_by, ":approved_at": datetime.now(UTC).isoformat()},
        )
        # SES dispatch belongs in the workflow worker after this durable approval transition.
        return {"action_id": action_id, "status": "approved", "approved_by": approved_by}
