"""Supervisor-led specialists using Bedrock Guardrails and cited research."""

from __future__ import annotations

from dataclasses import asdict
import logging
from typing import Any

from services.observability import trace
from services.search import SearchService
from services.supervisor import BedrockSupervisor


SPECIALIST_PROMPTS = {
    "schedule": "Analyze the supplied schedule rows. Preserve the documented risk calculation and identify high-risk equipment.",
    "political": "Assess geopolitical risks from the cited research and schedule context. Make no unsupported claims.",
    "tariff": "Assess tariffs, customs, and trade risks from the cited research and schedule context.",
    "logistics": "Assess route, port, carrier, and shipping risks from the cited research and schedule context.",
    "assistant": "Answer the user directly and concisely using the supplied context.",
    "reporting": "Produce a concise risk report. Every research-backed claim must cite a supplied source URL.",
}
logger = logging.getLogger(__name__)


class SpecialistOrchestrator:
    def __init__(self, supervisor_model_id: str, routine_model_id: str, guardrail_id: str, search: SearchService, client: Any = None) -> None:
        if client is None:
            import boto3
            client = boto3.client("bedrock-runtime")
        self._supervisor = BedrockSupervisor(supervisor_model_id, client, guardrail_id)
        self._routine_model_id, self._guardrail_id, self._search, self._client = routine_model_id, guardrail_id, search, client

    def run(self, question: str, schedule_rows: list[dict[str, Any]]) -> dict[str, Any]:
        with trace("supervisor.route"):
            decision = self._supervisor.decide(question)
        outputs: dict[str, str] = {}
        citations: list[dict[str, str | None]] = []
        for specialist in decision.specialists:
            if specialist == "reporting":
                continue
            research = [] if specialist == "schedule" else self._search.research(f"{specialist} procurement risk: {question}")
            citations.extend(asdict(item) for item in research)
            context = {"question": question, "schedule": schedule_rows, "sources": [asdict(item) for item in research]}
            with trace(f"specialist.{specialist}"):
                outputs[specialist] = self._invoke(specialist, context)
        report_context = {"question": question, "findings": outputs, "citations": citations}
        with trace("specialist.reporting"):
            report = self._invoke("reporting", report_context)
        return {"route": decision.specialists, "rationale": decision.rationale, "findings": outputs, "report": report, "citations": citations}

    def _invoke(self, specialist: str, context: dict[str, Any]) -> str:
        try:
            response = self._client.converse(
                modelId=self._routine_model_id,
                messages=[{"role": "user", "content": [{"text": f"{SPECIALIST_PROMPTS[specialist]}\n\nContext:\n{context}"}]}],
                inferenceConfig={"maxTokens": 1600, "temperature": 0.2},
                guardrailConfig={"guardrailIdentifier": self._guardrail_id, "guardrailVersion": "DRAFT", "trace": "enabled"},
            )
        except Exception as error:
            error_response = getattr(error, "response", {}) or {}
            error_details = error_response.get("Error", {}) if isinstance(error_response, dict) else {}
            logger.exception(
                "Bedrock specialist Converse failed model_id=%s region=%s specialist=%s guardrail_configured=%s error_type=%s error_code=%s",
                self._routine_model_id,
                getattr(getattr(self._client, "meta", None), "region_name", "unknown"),
                specialist,
                bool(self._guardrail_id),
                type(error).__name__,
                error_details.get("Code", "unknown"),
            )
            raise
        return response["output"]["message"]["content"][0]["text"]
