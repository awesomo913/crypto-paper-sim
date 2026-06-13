"""
Offline paper test: same rules as 03-live-aggressive-rsi-1m-paper.strat / live_12h_paper_rsi_ccxt.py:
  RSI(3), buy when RSI <= 47, sell when RSI >= 53, ~0.07% taker.
Uses bundled Binance historical CSV (no network). Bars are daily — for 1m behaviour run the live scripts on a network that can reach Binance.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

RSI_PERIOD = 3
RSI_LOW = 47.0
RSI_HIGH = 53.0
FEE = 0.0007
START_USDT = 1000.0


def positive_float(value: str, name: str) -> float:
    try:
        out = float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc
    if out <= 0:
        raise ValueError(f"{name} must be > 0")
    return out


def positive_int(value: str, name: str) -> int:
    try:
        out = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if out <= 0:
        raise ValueError(f"{name} must be > 0")
    return out


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    root = Path(__file__).resolve().parent.parent / "gocryptotrader" / "testdata"
    default_csv = root / "binance_BTCUSDT_24h_2019_01_01_2020_01_01.csv"
    parser = argparse.ArgumentParser(description="Run offline RSI paper simulation using local CSV candles.")
    parser.add_argument("--csv-path", type=Path, default=default_csv)
    parser.add_argument("--rsi-period", type=lambda v: positive_int(v, "rsi-period"), default=RSI_PERIOD)
    parser.add_argument("--rsi-low", type=lambda v: positive_float(v, "rsi-low"), default=RSI_LOW)
    parser.add_argument("--rsi-high", type=lambda v: positive_float(v, "rsi-high"), default=RSI_HIGH)
    parser.add_argument("--start-usdt", type=lambda v: positive_float(v, "start-usdt"), default=START_USDT)
    args = parser.parse_args(argv)
    if args.rsi_low >= args.rsi_high:
        parser.error("--rsi-low must be less than --rsi-high")
    return args


def rsi_simple(closes: list[float], period: int) -> float | None:
    if len(closes) < period + 1:
        return None
    gains = losses = 0.0
    for i in range(-period, 0):
        d = closes[i] - closes[i - 1]
        gains += max(d, 0.0)
        losses += max(-d, 0.0)
    l = losses / period
    if l == 0:
        return 100.0
    g = gains / period
    return 100.0 - (100.0 / (1.0 + g / l))


def main() -> None:
    args = parse_args()
    csv_path = args.csv_path
    if not csv_path.is_file():
        raise ValueError(f"CSV file not found: {csv_path}")
    closes: list[float] = []
    with csv_path.open() as f:
        for line_no, row in enumerate(csv.reader(f), start=1):
            if len(row) >= 6:
                try:
                    closes.append(float(row[5]))
                except ValueError as exc:
                    raise ValueError(f"Invalid close price on line {line_no} in {csv_path}") from exc
    if not closes:
        raise ValueError(
            f"No candle data found in {csv_path}. "
            "Verify the CSV exists and contains OHLCV rows with at least 6 columns."
        )

    usdt, btc = args.start_usdt, 0.0
    trades = 0
    for i in range(len(closes)):
        window = closes[: i + 1]
        r = rsi_simple(window, args.rsi_period)
        if r is None:
            continue
        price = closes[i]
        if r <= args.rsi_low and usdt > 5.0:
            cost = usdt * 0.999
            btc += (cost * (1.0 - FEE)) / price
            usdt = 0.0
            trades += 1
        elif r >= args.rsi_high and btc > 0.0:
            gross = btc * price
            usdt = gross * (1.0 - FEE)
            btc = 0.0
            trades += 1

    last = closes[-1]
    eq = usdt + btc * last
    print("Offline aggressive paper demo (GCT RSI rules; daily candles from bundled CSV)")
    print(f"  RSI_PERIOD={args.rsi_period} RSI_LOW={args.rsi_low} RSI_HIGH={args.rsi_high} fee={FEE}")
    print(f"  Start ${args.start_usdt:.2f}  End ${eq:.2f}  ({(eq / args.start_usdt - 1) * 100:+.2f}%)")
    print(f"  Trades: {trades}")
    print()
    print("For live paper on real 1m market data, run when Binance is reachable:")
    print("  crypto-paper-sim/live_12h_paper_rsi_ccxt.py  (set PAPER_TEST_HOURS=0.01 for a short probe)")


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2)
