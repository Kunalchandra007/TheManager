"""Runnable task implementation used by Step Functions and manual workflow starts."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4
from typing import Any

from services.observability import trace


class WorkflowRunner:
    def __init__(self, orchestrator: Any, schedule_repository: Any, state_repository: Any, report_service: Any) -> None:
        self._orchestrator, self._schedule, self._state, self._reports = orchestrator, schedule_repository, state_repository, report_service

    def run(self, question: str = "Generate the daily procurement risk report") -> dict[str, Any]:
        workflow_id = str(uuid4())
        self._state.put_workflow_status(workflow_id, {"status": "running", "stage": "analysis", "started_at": datetime.now(UTC).isoformat()})
        try:
            with trace("workflow.schedule"):
                schedule_rows = self._schedule.get_schedule_comparison()
            analysis = self._orchestrator.run(question, schedule_rows)
            with trace("workflow.report"):
                report = self._reports.create_and_upload(analysis["report"], workflow_id)
            result = {"workflow_id": workflow_id, "status": "completed", "stage": "completed", "report": report, "citations": analysis["citations"], "completed_at": datetime.now(UTC).isoformat()}
            self._state.put_workflow_status(workflow_id, result)
            return result
        except Exception as error:
            failure = {"workflow_id": workflow_id, "status": "failed", "stage": "failed", "error": str(error), "completed_at": datetime.now(UTC).isoformat()}
            self._state.put_workflow_status(workflow_id, failure)
            raise
