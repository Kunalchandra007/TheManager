import unittest

from services.search import SearchService


class Provider:
    def search(self, query: str) -> list[dict[str, str]]:
        return [{"title": "Port authority", "url": "https://example.test/notice", "snippet": query, "published_date": "2026-09-19"}]


class SearchTests(unittest.TestCase):
    def test_search_results_are_normalized_as_citations(self) -> None:
        results = SearchService(Provider(), min_interval_seconds=0).research("port closure")
        self.assertEqual(results[0].url, "https://example.test/notice")
        self.assertEqual(results[0].snippet, "port closure")
