import unittest

from simulate_30d import START, TAKER, Bar, rsi, sim_aggressive_rsi, sim_dca


def make_bars(prices: list[float]) -> list[Bar]:
    return [Bar(ts=i, vol=1.0, o=p, h=p, l=p, c=p) for i, p in enumerate(prices)]


class SimulationAccountingTests(unittest.TestCase):
    def test_aggressive_rsi_start_trades_and_pnl(self) -> None:
        bars = make_bars(
            [80.0, 90.0, 100.0, 110.0, 120.0, 130.0, 125.0, 120.0, 115.0, 110.0, 105.0, 110.0, 115.0, 120.0]
        )
        result = sim_aggressive_rsi(bars)

        expected_btc = (START * (1.0 - TAKER)) / 110.0
        expected_end = (expected_btc * 120.0) * (1.0 - TAKER)
        expected_pnl = (expected_end / START - 1.0) * 100.0

        self.assertEqual(result["start"], START)
        self.assertEqual(result["trades"], 2)
        self.assertAlmostEqual(result["end_equity"], expected_end, places=9)
        self.assertAlmostEqual(result["pnl_pct"], expected_pnl, places=9)

    def test_aggressive_bookkeeping_never_goes_negative(self) -> None:
        bars = make_bars(
            [80.0, 90.0, 100.0, 110.0, 120.0, 130.0, 125.0, 120.0, 115.0, 110.0, 105.0, 110.0, 115.0, 120.0]
        )

        usdt = START
        btc = 0.0
        closes: list[float] = []
        period, lo, hi = 5, 45.0, 55.0
        prev = None
        trades = 0
        for b in bars:
            closes.append(b.c)
            current = rsi(closes, period)
            if current is None:
                continue
            if prev is not None:
                if prev >= lo and current < lo and usdt > 1.0:
                    btc += (usdt * (1.0 - TAKER)) / b.c
                    usdt = 0.0
                    trades += 1
                elif prev <= hi and current > hi and btc > 0.0:
                    usdt = (btc * b.c) * (1.0 - TAKER)
                    btc = 0.0
                    trades += 1
            self.assertGreaterEqual(usdt, 0.0)
            self.assertGreaterEqual(btc, 0.0)
            prev = current

        result = sim_aggressive_rsi(bars)
        self.assertEqual(trades, result["trades"])
        self.assertAlmostEqual(usdt + btc * bars[-1].c, result["end_equity"], places=9)

    def test_dca_start_trades_and_pnl(self) -> None:
        bars = make_bars([10.0, 10.0, 10.0, 10.0])
        result = sim_dca(bars)

        spends = [250.0, 250.0, 250.0, 249.75]
        expected_btc = sum((spend * (1.0 - TAKER)) / 10.0 for spend in spends)
        expected_end = 0.25 + expected_btc * 10.0
        expected_pnl = (expected_end / START - 1.0) * 100.0

        self.assertEqual(result["start"], START)
        self.assertEqual(result["trades"], 4)
        self.assertAlmostEqual(result["end_equity"], expected_end, places=9)
        self.assertAlmostEqual(result["pnl_pct"], expected_pnl, places=9)

    def test_dca_bookkeeping_never_goes_negative(self) -> None:
        bars = make_bars([100.0, 90.0, 80.0, 70.0, 60.0, 50.0])
        usdt = START
        btc = 0.0
        per = START / len(bars)
        for b in bars:
            if usdt < 0.5:
                break
            spend = min(per, usdt * 0.999)
            if spend <= 0:
                break
            btc += spend * (1.0 - TAKER) / b.c
            usdt -= spend
            self.assertGreaterEqual(usdt, 0.0)
            self.assertGreaterEqual(btc, 0.0)

        result = sim_dca(bars)
        self.assertAlmostEqual(usdt + btc * bars[-1].c, result["end_equity"], places=9)


if __name__ == "__main__":
    unittest.main()
