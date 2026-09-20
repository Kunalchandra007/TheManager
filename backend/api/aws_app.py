"""Canonical FastAPI application for the AWS runtime.

This is the migration target; it deliberately does not import Azure/Semantic Kernel modules.
"""

from __future__ import annotations

from enum import StrEnum
import os
from functools import lru_cache
from uuid import uuid4
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from domain.what_if import simulate_delay
from config.aws_settings import AwsSettings
from repositories.aurora_data_api import AuroraDataApiRepository
from repositories.dynamo_state import DynamoStateRepository
from services.agents import SpecialistOrchestrator
from services.auth import require_authenticated_user
from services.search import SearchService
from services.tavily import TavilyProvider


class ErrorKind(StrEnum):
    DATABASE = "database_error"
    AI = "ai_error"
    TIMEOUT = "timeout_error"
    STORAGE = "storage_error"


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10_000)
    session_id: str | None = None


class WhatIfRequest(BaseModel):
    equipment_id: int
    days_variance: int
    days_until_due: int
    delay_days: int = Field(ge=0)


class ActionProposalRequest(BaseModel):
    supplier_email: str
    subject: str
    body: str
    evidence: list[dict[str, str]] = []


@lru_cache(maxsize=1)
def runtime() -> tuple[SpecialistOrchestrator, AuroraDataApiRepository, DynamoStateRepository]:
    settings = AwsSettings.from_environment()
    table_names = {
        "sessions": os.environ["SESSIONS_TABLE"], "events": os.environ["EVENTS_TABLE"],
        "workflow_runs": os.environ["WORKFLOW_RUNS_TABLE"],
    }
    search = SearchService(TavilyProvider(settings.tavily_secret_name, settings.region))
    agents = SpecialistOrchestrator(settings.supervisor_model_id, os.environ["BEDROCK_ROUTINE_MODEL_ID"], os.environ["BEDROCK_GUARDRAIL_ID"], search)
    return agents, AuroraDataApiRepository(settings.database_cluster_arn, settings.database_secret_arn), DynamoStateRepository(table_names)


def create_app(allowed_origins: list[str] | None = None) -> FastAPI:
    app = FastAPI(title="TheManager API", version="2.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins or ["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "themanager-api"}

    @app.post("/api/chat")
    async def chat(request: ChatRequest, user: dict[str, Any] = Depends(require_authenticated_user)) -> dict[str, Any]:
        try:
            session_id = request.session_id or str(uuid4())
            agents, schedules, state = runtime()
            state.put_session(session_id, request.message)
            result = agents.run(request.message, schedules.get_schedule_comparison())
            state.append_event({"event_id": str(uuid4()), "session_id": session_id, "agent_name": "supervisor", "action": "route", "route": result["route"], "user": user.get("sub")})
            return {"status": "success", "response": result["report"], "session_id": session_id, "citations": result["citations"]}
        except ValueError as error:
            raise HTTPException(status_code=503, detail={"kind": ErrorKind.DATABASE, "message": str(error)}) from error
        except Exception as error:
            raise HTTPException(status_code=502, detail={"kind": ErrorKind.AI, "message": str(error)}) from error

    @app.post("/workflow/run")
    async def run_workflow(_: dict[str, Any] = Depends(require_authenticated_user)) -> dict[str, str]:
        state_machine_arn = os.getenv("WORKFLOW_STATE_MACHINE_ARN")
        if not state_machine_arn:
            raise HTTPException(status_code=503, detail="Workflow is not configured")
        try:
            import boto3
            execution = boto3.client("stepfunctions").start_execution(stateMachineArn=state_machine_arn, input="{}")
            return {"status": "started", "execution_arn": execution["executionArn"]}
        except Exception as error:
            raise HTTPException(status_code=502, detail={"kind": ErrorKind.TIMEOUT, "message": str(error)}) from error

    @app.get("/api/sessions")
    async def sessions() -> dict[str, object]:
        return {"status": "success", "sessions": []}

    @app.get("/api/reports")
    async def reports() -> list[object]:
        return []

    @app.get("/api/heatmap")
    async def heatmap() -> list[object]:
        return []

    @app.get("/api/thinking-logs")
    async def thinking_logs() -> list[object]:
        return []

    @app.get("/workflow/status/{workflow_id}")
    async def workflow_status(workflow_id: str, _: dict[str, Any] = Depends(require_authenticated_user)) -> dict[str, Any]:
        _, _, state = runtime()
        return state.get_workflow_status(workflow_id) or {"workflow_id": workflow_id, "status": "not_found"}

    @app.post("/api/what-if")
    async def what_if(request: WhatIfRequest) -> dict[str, object]:
        result = simulate_delay(**request.model_dump())
        return {"equipment_id": result.equipment_id, "shifted_days": result.shifted_days, "before": result.before.__dict__, "after": result.after.__dict__}

    @app.get("/api/alerts")
    async def alerts() -> list[object]:
        return []

    @app.get("/api/actions")
    async def actions() -> list[object]:
        return []

    return app


app = create_app()
