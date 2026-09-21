"""Tavily adapter that reads its API key only from Secrets Manager at runtime."""

from __future__ import annotations

import json
from typing import Any

import requests


class TavilyProvider:
    def __init__(self, secret_name: str, region: str, secrets_client: Any = None, http_client: Any = requests) -> None:
        if secrets_client is None:
            import boto3
            secrets_client = boto3.client("secretsmanager", region_name=region)
        self._secret_name, self._secrets, self._http = secret_name, secrets_client, http_client

    def search(self, query: str) -> list[dict[str, Any]]:
        secret = self._secrets.get_secret_value(SecretId=self._secret_name)["SecretString"]
        try:
            key = json.loads(secret).get("api_key", secret)
        except json.JSONDecodeError:
            key = secret
        response = self._http.post("https://api.tavily.com/search", json={"api_key": key, "query": query, "search_depth": "advanced", "max_results": 5}, timeout=15)
        response.raise_for_status()
        return [{"title": item["title"], "url": item["url"], "snippet": item.get("content", ""), "published_date": item.get("published_date")} for item in response.json().get("results", [])]
