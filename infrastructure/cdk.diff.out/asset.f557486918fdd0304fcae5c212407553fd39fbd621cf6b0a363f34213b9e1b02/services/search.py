"""Provider-neutral, rate-limited search boundary for research specialists."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class Citation:
    title: str
    url: str
    snippet: str
    published_date: str | None = None


class SearchProvider(Protocol):
    def search(self, query: str) -> list[dict[str, Any]]: ...


class SearchService:
    def __init__(self, provider: SearchProvider, min_interval_seconds: float = 0.2, retries: int = 2) -> None:
        self._provider = provider
        self._min_interval = min_interval_seconds
        self._retries = retries
        self._last_request = 0.0

    def research(self, query: str) -> list[Citation]:
        remaining = self._min_interval - (time.monotonic() - self._last_request)
        if remaining > 0:
            time.sleep(remaining)
        for attempt in range(self._retries + 1):
            try:
                self._last_request = time.monotonic()
                return [Citation(str(item["title"]), str(item["url"]), str(item.get("snippet", "")), item.get("published_date")) for item in self._provider.search(query)]
            except Exception:
                if attempt == self._retries:
                    raise
                time.sleep(0.25 * (2**attempt))
        return []
