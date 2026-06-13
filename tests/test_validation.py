from __future__ import annotations

import unittest

import live_12h_paper_rsi_ccxt as live
import offline_aggressive_paper_demo as offline
import simulate_30d as sim30


class ValidationTests(unittest.TestCase):
    def test_live_symbol_validation_rejects_invalid(self) -> None:
        with self.assertRaises(ValueError):
            live.parse_symbol("BTCUSDT")

    def test_live_timeframe_validation_rejects_invalid(self) -> None:
        with self.assertRaises(ValueError):
            live.parse_timeframe("hourly")

    def test_live_parse_args_rejects_bad_rsi_range(self) -> None:
        with self.assertRaises(SystemExit):
            live.parse_args(["--rsi-low", "60", "--rsi-high", "40"])

    def test_offline_parse_args_rejects_bad_rsi_range(self) -> None:
        with self.assertRaises(SystemExit):
            offline.parse_args(["--rsi-low", "60", "--rsi-high", "40"])

    def test_sim_parse_args_rejects_bad_date_range(self) -> None:
        with self.assertRaises(SystemExit):
            sim30.parse_args(["--start-ts", "20", "--end-ts", "10"])

    def test_sim_days_validation(self) -> None:
        with self.assertRaises(ValueError):
            sim30.positive_int("0", "days")


if __name__ == "__main__":
    unittest.main()
