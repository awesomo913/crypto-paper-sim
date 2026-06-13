"""
30-day paper simulation: two separate $1,000 accounts on the same 30 daily candles.
Uses bundled GoCryptoTrader CSV (real Binance historical OHLCV) — no live API.
Does not use leverage; taker-fee 0.07% per trade (Binance spot-style).
"""
from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

# Same fee as our .strat overrides
TAKER = 0.0007
START = 1000.0
DAYS = 30


def positive_int(value: str, name: str) -> int:
    try:
        out = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if out <= 0:
        raise ValueError(f"{name} must be > 0")
    return out


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    root = Path(__file__).resolve().parent
    default_csv = root.parent / "gocryptotrader" / "testdata" / "binance_BTCUSDT_24h_2019_01_01_2020_01_01.csv"
    parser = argparse.ArgumentParser(description="Run 30-day offline paper simulation from historical CSV data.")
    parser.add_argument("--csv-path", type=Path, default=default_csv)
    parser.add_argument("--days", type=lambda v: positive_int(v, "days"), default=DAYS)
    parser.add_argument("--start-ts", type=int, default=None, help="Optional start unix timestamp filter.")
    parser.add_argument("--end-ts", type=int, default=None, help="Optional end unix timestamp filter.")
    args = parser.parse_args(argv)
    if args.start_ts is not None and args.end_ts is not None and args.start_ts > args.end_ts:
        parser.error("--start-ts must be <= --end-ts")
    return args


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
        for line_no, row in enumerate(csv.reader(f), start=1):
            if not row or len(row) < 6:
                continue
            try:
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
            except ValueError as exc:
                raise ValueError(f"Invalid CSV data on line {line_no} in {p}") from exc
    return out


def rsi(closes: list[float], period: int) -> float | None:
    if len(closes) < period + 1:
        return None
    window = closes[-(period + 1) :]
    gains = 0.0
    losses = 0.0
    for i in range(1, len(window)):
        d = window[i] - window[i - 1]
        if d > 0:
            gains += d
        else:
            losses += -d
    avg_g = gains / period
    avg_l = losses / period
    if avg_l == 0:
        return 100.0
    rs = avg_g / avg_l
    return 100.0 - (100.0 / (1.0 + rs))


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
        r = rsi(closes, period)
        if r is None:
            continue
        if prev is not None:
            if prev >= lo and r < lo and usdt > 1.0:
                q = (usdt * (1.0 - TAKER)) / b.c
                btc += q
                usdt = 0.0
                trades += 1
            elif prev <= hi and r > hi and btc > 0.0:
                gross = btc * b.c
                usdt = gross * (1.0 - TAKER)
                btc = 0.0
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
        q = spend * (1.0 - TAKER) / b.c
        btc += q
        usdt -= spend
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
    args = parse_args()
    gct = args.csv_path
    if not gct.is_file():
        print(f"Missing CSV: {gct}")
        print("Clone gocryptotrader so testdata/ exists, or pass --csv-path.")
        raise SystemExit(1)

    all_bars = load_csv(gct)
    if args.start_ts is not None:
        all_bars = [b for b in all_bars if b.ts >= args.start_ts]
    if args.end_ts is not None:
        all_bars = [b for b in all_bars if b.ts <= args.end_ts]
    if not all_bars:
        raise ValueError("No candles left after applying timestamp filters")
    if args.days > len(all_bars):
        raise ValueError(f"Requested --days={args.days} but only {len(all_bars)} candles are available")
    bars = all_bars[-args.days :]

    a = sim_aggressive_rsi(bars)
    d = sim_dca(bars)
    first_ts, last_ts = bars[0].ts, bars[-1].ts

    print(f"Simulation window from CSV: {gct}")
    print(f"  From unix {first_ts} to {last_ts} ({len(bars)} candles)")
    print()
    for x in (a, d):
        print(x["name"])
        print(f"  Start:   ${x['start']:.2f} (paper)")
        print(f"  End:     ${x['end_equity']:.2f}  ({x['pnl_pct']:+.2f}%)")
        print(f"  Trades:  {x['trades']}")
        print()


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2)
