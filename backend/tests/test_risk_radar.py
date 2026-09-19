import unittest

from domain.risk_radar import RiskFinding, new_or_worsened


class TheManagerRiskTests(unittest.TestCase):
    def test_only_new_or_worsened_risks_alert(self) -> None:
        old = RiskFinding("EQ-1", "Germany", "logistics", 3, "Port congestion")
        unchanged = RiskFinding("EQ-1", "Germany", "logistics", 3, "Port congestion")
        worse = RiskFinding("EQ-1", "Germany", "logistics", 5, "Port closed")
        new = RiskFinding("EQ-2", "China", "political", 4, "Restriction")
        self.assertEqual(new_or_worsened([unchanged, worse, new], [old]), [worse, new])
