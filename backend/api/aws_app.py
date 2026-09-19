"""Canonical FastAPI application for the AWS runtime.

This is the migration target; it deliberately does not import Azure/Semantic Kernel modules.
"""

from __future__ import annotations

from enum import StrEnum
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from domain.what_if import simulate_delay


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
    async def chat(request: ChatRequest) -> dict[str, str]:
        # Invocation is wired by Lambda configuration in Phase 4; response shape stays stable now.
        return {"status": "accepted", "response": "AWS agent runtime is not configured.", "session_id": request.session_id or str(uuid4())}

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
    async def workflow_status(workflow_id: str) -> dict[str, str]:
        return {"workflow_id": workflow_id, "status": "not_found"}

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
