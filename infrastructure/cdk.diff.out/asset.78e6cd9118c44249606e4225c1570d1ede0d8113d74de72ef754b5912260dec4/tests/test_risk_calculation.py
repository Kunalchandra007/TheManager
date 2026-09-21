import unittest

from domain.risk_calculation import assess, calculate_percentage


class RiskCalculationTests(unittest.TestCase):
    def test_low_risk_is_below_five_percent(self) -> None:
        result = assess(4, 100)
        self.assertEqual(result.percentage, 4.0)
        self.assertEqual((result.flag, result.points), ("Low Risk", 1))

    def test_exactly_five_percent_is_medium_risk(self) -> None:
        result = assess(5, 100)
        self.assertEqual((result.flag, result.points), ("Medium Risk", 3))

    def test_exactly_fifteen_percent_is_high_risk(self) -> None:
        result = assess(15, 100)
        self.assertEqual((result.flag, result.points), ("High Risk", 5))

    def test_overdue_milestone_is_one_hundred_percent(self) -> None:
        self.assertEqual(calculate_percentage(1, 0), 100.0)


if __name__ == "__main__":
    unittest.main()
