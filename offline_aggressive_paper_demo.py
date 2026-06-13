"""
Offline paper test: same rules as 03-live-aggressive-rsi-1m-paper.strat / live_12h_paper_rsi_ccxt.py:
  RSI(3), buy when RSI <= 47, sell when RSI >= 53, ~0.07% taker.
Uses bundled Binance historical CSV (no network). Bars are daily — for 1m behaviour run the live scripts on a network that can reach Binance.
"""
from __future__ import annotations

import csv
from pathlib import Path

from paper_sim.core import buy_all, rsi_last, sell_all

RSI_PERIOD = 3
RSI_LOW = 47.0
RSI_HIGH = 53.0
FEE = 0.0007
START_USDT = 1000.0


def main() -> None:
    root = Path(__file__).resolve().parent.parent / "gocryptotrader" / "testdata"
    csv_path = root / "binance_BTCUSDT_24h_2019_01_01_2020_01_01.csv"
    closes: list[float] = []
    with csv_path.open() as f:
        for row in csv.reader(f):
            if len(row) >= 6:
                closes.append(float(row[5]))

    usdt, btc = START_USDT, 0.0
    trades = 0
    for i in range(len(closes)):
        window = closes[: i + 1]
        r = rsi_last(window, RSI_PERIOD)
        if r is None:
            continue
        price = closes[i]
        if r <= RSI_LOW and usdt > 5.0:
            usdt, btc = buy_all(usdt=usdt, btc=btc, price=price, fee=FEE, reserve=0.999)
            trades += 1
        elif r >= RSI_HIGH and btc > 0.0:
            usdt, btc = sell_all(usdt=usdt, btc=btc, price=price, fee=FEE)
            trades += 1

    last = closes[-1]
    eq = usdt + btc * last
    print("Offline aggressive paper demo (GCT RSI rules; daily candles from bundled CSV)")
    print(f"  RSI_PERIOD={RSI_PERIOD} RSI_LOW={RSI_LOW} RSI_HIGH={RSI_HIGH} fee={FEE}")
    print(f"  Start ${START_USDT:.2f}  End ${eq:.2f}  ({(eq / START_USDT - 1) * 100:+.2f}%)")
    print(f"  Trades: {trades}")
    print()
    print("For live paper on real 1m market data, run when Binance is reachable:")
    print("  crypto-paper-sim/live_12h_paper_rsi_ccxt.py  (set PAPER_TEST_HOURS=0.01 for a short probe)")


if __name__ == "__main__":
    main()
