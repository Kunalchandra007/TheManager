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
            if os.getenv("DEMO_MODE", "false").lower() == "true":
                return {
                    "status": "success",
                    "response": (
                        "## Procurement Risk Assessment\n\n"
                        "### Executive Summary\n"
                        "The supply chain is exposed to four connected risk areas: schedule delays, "
                        "supplier concentration, geopolitical disruption, and logistics bottlenecks. "
                        "These risks can reinforce one another: a delayed supplier shipment may require "
                        "an alternate route, while a geopolitical event can reduce carrier availability "
                        "and extend delivery times. The recommended approach is to monitor early-warning "
                        "signals, protect critical items with contingency options, and review the plan "
                        "weekly for high-impact changes.\n\n"
                        "### 1. Schedule and Delivery Risk\n"
                        "Late milestones are the most immediate operational concern. Pay particular "
                        "attention to overdue manufacturing starts, inspection dates, export clearance, "
                        "and confirmed delivery milestones. A small delay at the beginning of the chain "
                        "can become significant once production, consolidation, customs, and final-mile "
                        "transport are combined. Track planned versus actual dates, days of variance, "
                        "and the number of remaining recovery opportunities for each critical item.\n\n"
                        "Recommended actions: create an escalation threshold for late milestones, require "
                        "suppliers to provide recovery plans, and maintain a clear list of items whose "
                        "delay would affect project commissioning or customer commitments.\n\n"
                        "### 2. Supplier Concentration Risk\n"
                        "Dependence on a single supplier, factory, region, or sub-tier component creates "
                        "a single point of failure. Even when the primary supplier is performing well, "
                        "capacity constraints, quality problems, labor disruption, or raw-material "
                        "shortages can interrupt the entire schedule. Concentration risk is highest for "
                        "long-lead equipment and parts with limited substitutes.\n\n"
                        "Recommended actions: qualify backup suppliers for critical categories, verify "
                        "their production capacity and lead times, and identify components that cannot be "
                        "replaced quickly. Where dual sourcing is not practical, hold appropriate safety "
                        "stock or negotiate reserved production capacity.\n\n"
                        "### 3. Geopolitical and Trade Risk\n"
                        "Changes in sanctions, tariffs, export controls, customs requirements, labor "
                        "conditions, or regional stability can affect both cost and delivery reliability. "
                        "The risk is not limited to the supplier's headquarters: the origin country, transit "
                        "countries, ports, and the destination market may all introduce constraints.\n\n"
                        "Recommended actions: review country and route exposure before placing urgent orders, "
                        "maintain current trade documentation, confirm alternate sourcing locations, and "
                        "define an escalation process for regulatory or geopolitical changes. Include cost "
                        "sensitivity checks for tariff changes and additional customs handling.\n\n"
                        "### 4. Logistics and Transportation Risk\n"
                        "Port congestion, carrier capacity, missed connections, weather, equipment shortages, "
                        "and customs delays can make an otherwise ready shipment late. Logistics risk is "
                        "especially material when there is only one viable port, carrier, route, or delivery "
                        "window. A low-cost route may carry a higher schedule risk if it has limited recovery "
                        "options.\n\n"
                        "Recommended actions: review alternate ports and carriers, confirm booking and "
                        "container availability early, track estimated versus actual transit times, and "
                        "pre-approve expedited or alternate routing for critical shipments.\n\n"
                        "### Priority Actions for the Next Review Cycle\n"
                        "1. Identify the five items with the greatest schedule impact and assign owners.\n"
                        "2. Confirm backup suppliers or recovery plans for single-source critical items.\n"
                        "3. Review geopolitical, tariff, and customs exposure for active routes.\n"
                        "4. Validate alternate carrier, port, and final-mile options.\n"
                        "5. Set measurable alerts for milestone slippage, supplier delay, and transit variance.\n\n"
                        "### Overall Assessment\n"
                        "The highest near-term exposure comes from the interaction between schedule variance "
                        "and limited recovery options. Reducing supplier concentration and preparing alternate "
                        "routes will improve resilience, while milestone monitoring will provide the earliest "
                        "opportunity to intervene. This assessment is a demonstration response using sample "
                        "data; production decisions should be supported by current supplier, schedule, and "
                        "logistics records."
                    ),
                    "session_id": session_id,
                    "citations": [],
                }

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
