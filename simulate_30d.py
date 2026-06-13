"""
30-day paper simulation: two separate $1,000 accounts on the same 30 daily candles.
Uses bundled GoCryptoTrader CSV (real Binance historical OHLCV) — no live API.
Does not use leverage; taker-fee 0.07% per trade (Binance spot-style).
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from paper_sim.core import buy_all, buy_spend, rsi_last, sell_all

# Same fee as our .strat overrides
TAKER = 0.0007
START = 1000.0
DAYS = 30


@dataclass
class Bar:
    ts: int
    vol: float
    o: float
    h: float
    l: float
    c: float


def load_csv(p: Path) -> list[Bar]:
    out: list[Bar] = []
    with p.open(newline="") as f:
        for row in csv.reader(f):
            if not row or len(row) < 6:
                continue
            out.append(
                Bar(
                    int(float(row[0])),
                    float(row[1]),
                    float(row[2]),
                    float(row[3]),
                    float(row[4]),
                    float(row[5]),
                )
            )
    return out

def sim_aggressive_rsi(bars: list[Bar]) -> dict:
    """Fast RSI(5), tight 45/55 — aggressive: trade into/out of BTC on each signal."""
    usdt = START
    btc = 0.0
    trades = 0
    closes: list[float] = []
    period, lo, hi = 5, 45.0, 55.0
    prev: float | None = None

    for b in bars:
        closes.append(b.c)
        r = rsi_last(closes, period)
        if r is None:
            continue
        if prev is not None:
            if prev >= lo and r < lo and usdt > 1.0:
                usdt, btc = buy_all(usdt=usdt, btc=btc, price=b.c, fee=TAKER)
                trades += 1
            elif prev <= hi and r > hi and btc > 0.0:
                usdt, btc = sell_all(usdt=usdt, btc=btc, price=b.c, fee=TAKER)
                trades += 1
        prev = r

    last = bars[-1].c
    equity = usdt + btc * last
    return {
        "name": "Aggressive RSI (5m-style on daily bar proxy)",
        "start": START,
        "end_equity": equity,
        "pnl_pct": (equity / START - 1.0) * 100.0,
        "trades": trades,
    }


def sim_dca(bars: list[Bar]) -> dict:
    """Dollar-cost average: invest START over each candle equally."""
    usdt = START
    btc = 0.0
    per = START / len(bars)
    for b in bars:
        if usdt < 0.5:
            break
        spend = min(per, usdt * 0.999)
        if spend <= 0:
            break
        usdt, btc = buy_spend(usdt=usdt, btc=btc, price=b.c, fee=TAKER, spend=spend)
    last = bars[-1].c
    equity = usdt + btc * last
    return {
        "name": "Long-term DCA (buy each day)",
        "start": START,
        "end_equity": equity,
        "pnl_pct": (equity / START - 1.0) * 100.0,
        "trades": len(bars),
    }


def main() -> None:
    root = Path(__file__).resolve().parent
    gct = root.parent / "gocryptotrader" / "testdata" / "binance_BTCUSDT_24h_2019_01_01_2020_01_01.csv"
    if not gct.is_file():
        print(f"Missing CSV: {gct}")
        print("Clone gocryptotrader so testdata/ exists, or set CSV path in script.")
        raise SystemExit(1)

    all_bars = load_csv(gct)
    bars = all_bars[-DAYS:]

    a = sim_aggressive_rsi(bars)
    d = sim_dca(bars)
    first_ts, last_ts = bars[0].ts, bars[-1].ts

    print("30-day window (last rows of bundled Binance BTCUSDT daily CSV)")
    print(f"  From unix {first_ts} to {last_ts} ({DAYS} candles)")
    print()
    for x in (a, d):
        print(x["name"])
        print(f"  Start:   ${x['start']:.2f} (paper)")
        print(f"  End:     ${x['end_equity']:.2f}  ({x['pnl_pct']:+.2f}%)")
        print(f"  Trades:  {x['trades']}")
        print()


if __name__ == "__main__":
    main()
