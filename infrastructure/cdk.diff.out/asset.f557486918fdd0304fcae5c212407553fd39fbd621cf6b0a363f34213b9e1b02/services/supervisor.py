"""Bedrock supervisor that uses structured routes, not keyword-only routing."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Callable


SPECIALISTS = ("schedule", "political", "tariff", "logistics", "reporting", "assistant")
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SupervisorDecision:
    specialists: list[str]
    rationale: str


class BedrockSupervisor:
    """Requests a JSON routing decision from Bedrock and validates its shape."""

    def __init__(self, model_id: str, client: Any = None, guardrail_id: str | None = None) -> None:
        self.model_id = model_id
        if client is None:
            import boto3

            client = boto3.client("bedrock-runtime")
        self._client = client
        self._guardrail_id = guardrail_id

    def decide(self, question: str) -> SupervisorDecision:
        prompt = (
            "Choose one or more specialists for this procurement-risk question. "
            f"Allowed specialists: {', '.join(SPECIALISTS)}. Return JSON only with "
            '{"specialists":[...],"rationale":"..."}. Question: ' + question
        )
        request: dict[str, Any] = {
            "modelId": self.model_id,
            "messages": [{"role": "user", "content": [{"text": prompt}]}],
            "inferenceConfig": {"maxTokens": 180, "temperature": 0},
        }
        if self._guardrail_id:
            request["guardrailConfig"] = {
                "guardrailIdentifier": self._guardrail_id,
                "guardrailVersion": "DRAFT",
                "trace": "enabled",
            }
        try:
            response = self._client.converse(**request)
        except Exception as error:
            error_response = getattr(error, "response", {}) or {}
            error_details = error_response.get("Error", {}) if isinstance(error_response, dict) else {}
            logger.exception(
                "Bedrock supervisor Converse failed model_id=%s region=%s error_type=%s error_code=%s",
                self.model_id,
                getattr(getattr(self._client, "meta", None), "region_name", "unknown"),
                type(error).__name__,
                error_details.get("Code", "unknown"),
            )
            raise
        text = response["output"]["message"]["content"][0]["text"]
        payload = json.loads(text)
        specialists = [name for name in payload.get("specialists", []) if name in SPECIALISTS]
        if not specialists:
            raise ValueError("Bedrock supervisor returned no supported specialists")
        return SupervisorDecision(specialists=specialists, rationale=str(payload.get("rationale", "")))
