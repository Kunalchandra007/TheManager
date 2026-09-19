import unittest

from api.aws_app import create_app


class AwsApiTests(unittest.TestCase):
    def test_canonical_routes_are_registered(self) -> None:
        paths = {route.path for route in create_app().routes}
        self.assertTrue({"/health", "/api/chat", "/api/sessions", "/api/reports", "/api/heatmap", "/api/thinking-logs", "/api/what-if"}.issubset(paths))


if __name__ == "__main__":
    unittest.main()
