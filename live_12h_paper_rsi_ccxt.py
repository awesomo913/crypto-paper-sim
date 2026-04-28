"""
12-hour paper test: mirrors GCT RSI — buy when RSI <= rsi-low, sell when RSI >= rsi-high
(see gocryptotrader/backtester/eventhandlers/strategies/rsi/rsi.go).
1m BTC/USDT, no API keys (public klines only). Stops after 12h wall time or Ctrl+C.
pip install ccxt
"""
from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
try:
    import ccxt
except ImportError:
    print("pip install ccxt", file=sys.stderr)
    raise SystemExit(1)

RSI_PERIOD = 3
RSI_LOW = 47.0
RSI_HIGH = 53.0
FEE = 0.0007
SYMBOL = "BTC/USDT"
TF = "1m"
HOURS = float(os.environ.get("PAPER_TEST_HOURS", "12"))
POLL_S = 15
START_USDT = 1000.0


def rsi_last(closes: list[float], period: int) -> float | None:
    if len(closes) < period + 1:
        return None
    gains = 0.0
    losses = 0.0
    for i in range(-period, 0):
        d = closes[i] - closes[i - 1]
        if d > 0:
            gains += d
        else:
            losses += -d
    g = gains / period
    l = losses / period
    if l == 0:
        return 100.0
    rs = g / l
    return 100.0 - (100.0 / (1.0 + rs))


@dataclass
class Paper:
    usdt: float = START_USDT
    btc: float = 0.0
    trades: int = 0
    last_candle_ms: int | None = None

    def mark(self, price: float) -> float:
        return self.usdt + self.btc * price

    def apply(self, price: float, r: float) -> None:
        if r <= RSI_LOW and self.usdt > 5.0:
            cost = self.usdt * 0.999
            self.btc += (cost * (1.0 - FEE)) / price
            self.usdt = 0.0
            self.trades += 1
        elif r >= RSI_HIGH and self.btc > 0.0:
            gross = self.btc * price
            self.usdt = gross * (1.0 - FEE)
            self.btc = 0.0
            self.trades += 1


def main() -> None:
    ex = ccxt.binance({"enableRateLimit": True})
    end = time.time() + HOURS * 3600
    p = Paper()
    print(
        f"PAPER ({HOURS:g}h) | {SYMBOL} {TF} | {START_USDT} USDT | "
        f"RSI({RSI_PERIOD}) buy<={RSI_LOW} sell>={RSI_HIGH} (matches GCT) | Ctrl+C to stop"
    )
    while time.time() < end:
        try:
            ohlcv = ex.fetch_ohlcv(SYMBOL, TF, limit=80)
        except Exception as e:
            print(f"fetch: {e}; sleep 10s")
            time.sleep(10)
            continue
        if not ohlcv:
            time.sleep(POLL_S)
            continue
        ts, _, _, _, c, _ = ohlcv[-1]
        if p.last_candle_ms == ts:
            time.sleep(POLL_S)
            continue
        p.last_candle_ms = int(ts)
        closes = [float(x[4]) for x in ohlcv]
        r = rsi_last(closes, RSI_PERIOD)
        if r is None:
            time.sleep(POLL_S)
            continue
        price = float(c)
        p.apply(price, r)
        print(
            f"equity=${p.mark(price):,.2f} usdt={p.usdt:.2f} btc={p.btc:.6f} "
            f"RSI={r:.2f} trades={p.trades}"
        )
        time.sleep(POLL_S)
    ohlcv = ex.fetch_ohlcv(SYMBOL, TF, limit=1)
    px = float(ohlcv[-1][4]) if ohlcv else 0.0
    print(f"Done. Final ~${p.mark(px):,.2f} trades={p.trades}")


if __name__ == "__main__":
    main()
