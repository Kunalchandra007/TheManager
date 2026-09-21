import unittest

from domain.what_if import simulate_delay


class WhatIfTests(unittest.TestCase):
    def test_delay_can_change_a_category(self) -> None:
        result = simulate_delay(equipment_id=7, days_variance=4, days_until_due=100, delay_days=11)
        self.assertEqual(result.before.flag, "Low Risk")
        self.assertEqual(result.after.flag, "High Risk")

    def test_negative_delay_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            simulate_delay(1, 1, 10, -1)
