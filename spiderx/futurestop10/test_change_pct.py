import unittest
from decimal import Decimal

from main import calculate_change_pct, filter_top10


class CalculateChangePctTest(unittest.TestCase):
    def test_computes_percent_from_today_and_yesterday_close(self):
        self.assertEqual(calculate_change_pct(159600, 152020), 4.99)
        self.assertEqual(calculate_change_pct(5471, 5738), -4.65)
        self.assertEqual(calculate_change_pct(Decimal("3112.00"), Decimal("3088.00")), 0.78)

    def test_returns_none_when_yesterday_close_missing_or_zero(self):
        self.assertIsNone(calculate_change_pct(100, None))
        self.assertIsNone(calculate_change_pct(100, 0))
        self.assertIsNone(calculate_change_pct(None, 100))


class FilterTop10UsesComputedChangePctTest(unittest.TestCase):
    def test_keeps_contracts_above_one_percent_even_if_db_field_was_zero(self):
        data = [
            {"symbol": "LCM", "name": "碳酸锂", "price": "159600", "change_pct": 4.99},
            {"symbol": "RSM", "name": "菜粕", "price": "5471", "change_pct": -4.65},
            {"symbol": "RBM", "name": "螺纹钢", "price": "3112", "change_pct": 0.78},
        ]
        result = filter_top10(data)
        self.assertEqual([item["contract"] for item in result["top_gainers"]], ["LCM"])
        self.assertEqual([item["contract"] for item in result["top_losers"]], ["RSM"])


if __name__ == "__main__":
    unittest.main()
