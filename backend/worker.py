"""Lambda task handler for the durable TheManager workflow."""

from __future__ import annotations

from api.aws_app import runtime
from services.reports import S3ReportService
from services.workflow_runner import WorkflowRunner
import os


def handler(event: dict, _: object) -> dict:
    agents, schedules, state = runtime()
    runner = WorkflowRunner(agents, schedules, state, S3ReportService(os.environ["REPORT_BUCKET"]))
    return runner.run(event.get("question", "Generate the daily procurement risk report"))
