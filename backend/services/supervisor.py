"""Bedrock supervisor that uses structured routes, not keyword-only routing."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable


SPECIALISTS = ("schedule", "political", "tariff", "logistics", "reporting", "assistant")


@dataclass(frozen=True)
class SupervisorDecision:
    specialists: list[str]
    rationale: str


class BedrockSupervisor:
    """Requests a JSON routing decision from Bedrock and validates its shape."""

    def __init__(self, model_id: str, client: Any = None) -> None:
        self.model_id = model_id
        if client is None:
            import boto3

            client = boto3.client("bedrock-runtime")
        self._client = client

    def decide(self, question: str) -> SupervisorDecision:
        prompt = (
            "Choose one or more specialists for this procurement-risk question. "
            f"Allowed specialists: {', '.join(SPECIALISTS)}. Return JSON only with "
            '{"specialists":[...],"rationale":"..."}. Question: ' + question
        )
        response = self._client.converse(
            modelId=self.model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 180, "temperature": 0},
        )
        text = response["output"]["message"]["content"][0]["text"]
        payload = json.loads(text)
        specialists = [name for name in payload.get("specialists", []) if name in SPECIALISTS]
        if not specialists:
            raise ValueError("Bedrock supervisor returned no supported specialists")
        return SupervisorDecision(specialists=specialists, rationale=str(payload.get("rationale", "")))
