"""Aurora PostgreSQL Data API adapter with parameterized statements only."""

from __future__ import annotations

from datetime import date
from typing import Any


class AuroraDataApiRepository:
    """Small repository for schedule reads and S3 report metadata writes."""

    def __init__(self, resource_arn: str, secret_arn: str, database: str = "themanager", client: Any = None) -> None:
        if not resource_arn or not secret_arn:
            raise ValueError("Aurora resource ARN and secret ARN are required")
        if client is None:
            import boto3

            client = boto3.client("rds-data")
        self._client = client
        self._arguments = {"resourceArn": resource_arn, "secretArn": secret_arn, "database": database}

    def get_schedule_comparison(self, equipment_id: int | None = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM v_schedule_comparison"
        parameters: list[dict[str, Any]] = []
        if equipment_id is not None:
            sql += " WHERE equipment_id = :equipment_id"
            parameters.append({"name": "equipment_id", "value": {"longValue": equipment_id}})
        response = self._client.execute_statement(
            **self._arguments, sql=sql, parameters=parameters, includeResultMetadata=True
        )
        columns = [column["name"] for column in response.get("columnMetadata", [])]
        return [dict(zip(columns, (self._value(field) for field in row))) for row in response.get("records", [])]

    def save_report(self, session_id: str, conversation_id: str, filename: str, s3_key: str, report_type: str) -> None:
        self._client.execute_statement(
            **self._arguments,
            sql=("INSERT INTO fact_risk_report (session_id, conversation_id, filename, s3_key, report_type) "
                 "VALUES (:session_id, CAST(:conversation_id AS UUID), :filename, :s3_key, :report_type)"),
            parameters=[
                {"name": "session_id", "value": {"stringValue": session_id}},
                {"name": "conversation_id", "value": {"stringValue": conversation_id}},
                {"name": "filename", "value": {"stringValue": filename}},
                {"name": "s3_key", "value": {"stringValue": s3_key}},
                {"name": "report_type", "value": {"stringValue": report_type}},
            ],
        )

    @staticmethod
    def _value(field: dict[str, Any]) -> Any:
        if field.get("isNull"):
            return None
        for key in ("stringValue", "longValue", "doubleValue", "booleanValue"):
            if key in field:
                return field[key]
        return field.get("arrayValue")
