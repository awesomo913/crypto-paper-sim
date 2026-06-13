from __future__ import annotations

import unittest

from paper_sim.core import buy_all, buy_spend, rsi_last, sell_all


class PaperSimCoreTests(unittest.TestCase):
    def test_rsi_last_matches_flat_series(self) -> None:
        closes = [100.0, 100.0, 100.0, 100.0]
        self.assertEqual(rsi_last(closes, 3), 100.0)

    def test_buy_and_sell_accounting(self) -> None:
        usdt, btc = buy_all(usdt=1000.0, btc=0.0, price=100.0, fee=0.0007, reserve=0.999)
        self.assertEqual(usdt, 0.0)
        self.assertAlmostEqual(btc, (999.0 * (1.0 - 0.0007)) / 100.0)
        usdt, btc = sell_all(usdt=usdt, btc=btc, price=100.0, fee=0.0007)
        self.assertEqual(btc, 0.0)
        self.assertAlmostEqual(usdt, 999.0 * (1.0 - 0.0007) * (1.0 - 0.0007))

    def test_buy_spend_accounting(self) -> None:
        usdt, btc = buy_spend(usdt=1000.0, btc=0.0, price=200.0, fee=0.0007, spend=100.0)
        self.assertAlmostEqual(usdt, 900.0)
        self.assertAlmostEqual(btc, (100.0 * (1.0 - 0.0007)) / 200.0)


if __name__ == "__main__":
    unittest.main()

