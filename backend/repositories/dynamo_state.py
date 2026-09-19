"""DynamoDB state adapter; live conversation state survives process restarts."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any


class DynamoStateRepository:
    def __init__(self, table_names: dict[str, str], resource: Any = None) -> None:
        if resource is None:
            import boto3

            resource = boto3.resource("dynamodb")
        self._tables = {name: resource.Table(table_name) for name, table_name in table_names.items()}

    def put_session(self, session_id: str, message: str, ttl_days: int = 30) -> None:
        now = datetime.now(UTC)
        self._tables["sessions"].put_item(Item={
            "session_id": session_id, "first_query": message, "updated_at": now.isoformat(),
            "expires_at": int((now + timedelta(days=ttl_days)).timestamp()),
        })

    def append_event(self, event: dict[str, Any]) -> None:
        self._tables["events"].put_item(Item=event)

    def put_workflow_status(self, workflow_id: str, status: dict[str, Any]) -> None:
        self._tables["workflow_runs"].put_item(Item={"workflow_id": workflow_id, **status})

    def get_workflow_status(self, workflow_id: str) -> dict[str, Any] | None:
        return self._tables["workflow_runs"].get_item(Key={"workflow_id": workflow_id}).get("Item")
