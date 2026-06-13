import unittest

from simulate_30d import rsi


class RSILogicTests(unittest.TestCase):
    def test_known_fixture_matches_hand_computed_value(self) -> None:
        closes = [1.0, 2.0, 3.0, 2.0, 2.0, 4.0]
        self.assertAlmostEqual(rsi(closes, 5), 80.0, places=9)

    def test_flat_prices_returns_100(self) -> None:
        self.assertEqual(rsi([10.0, 10.0, 10.0, 10.0, 10.0, 10.0], 5), 100.0)

    def test_all_up_returns_100(self) -> None:
        self.assertEqual(rsi([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], 5), 100.0)

    def test_all_down_returns_0(self) -> None:
        self.assertEqual(rsi([6.0, 5.0, 4.0, 3.0, 2.0, 1.0], 5), 0.0)

    def test_too_few_points_returns_none(self) -> None:
        self.assertIsNone(rsi([1.0, 2.0, 3.0, 4.0], 5))


if __name__ == "__main__":
    unittest.main()
