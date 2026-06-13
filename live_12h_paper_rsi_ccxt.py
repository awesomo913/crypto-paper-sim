"""
12-hour paper test: mirrors GCT RSI — buy when RSI <= rsi-low, sell when RSI >= rsi-high
(see gocryptotrader/backtester/eventhandlers/strategies/rsi/rsi.go).
1m BTC/USDT, no API keys (public klines only). Stops after 12h wall time or Ctrl+C.
pip install ccxt
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time
from dataclasses import dataclass

RSI_PERIOD = 3
RSI_LOW = 47.0
RSI_HIGH = 53.0
FEE = 0.0007
SYMBOL = "BTC/USDT"
TF = "1m"
HOURS = float(os.environ.get("PAPER_TEST_HOURS", "12"))
POLL_S = 15
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


def parse_symbol(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9._-]+/[A-Za-z0-9._-]+", value):
        raise ValueError("symbol must use BASE/QUOTE format (example: BTC/USDT)")
    return value.upper()


def parse_timeframe(value: str) -> str:
    if not re.fullmatch(r"\d+[mhdwM]", value):
        raise ValueError("timeframe must look like 1m, 5m, 1h, 1d, 1w, or 1M")
    return value


def config_from_env() -> dict[str, float | int | str]:
    return {
        "hours": positive_float(os.environ.get("PAPER_TEST_HOURS", str(HOURS)), "hours"),
        "symbol": parse_symbol(os.environ.get("PAPER_TEST_SYMBOL", SYMBOL)),
        "timeframe": parse_timeframe(os.environ.get("PAPER_TEST_TIMEFRAME", TF)),
        "poll_seconds": positive_float(os.environ.get("PAPER_TEST_POLL_S", str(POLL_S)), "poll-seconds"),
        "start_usdt": positive_float(os.environ.get("PAPER_TEST_START_USDT", str(START_USDT)), "start-usdt"),
        "rsi_period": positive_int(os.environ.get("PAPER_TEST_RSI_PERIOD", str(RSI_PERIOD)), "rsi-period"),
        "rsi_low": positive_float(os.environ.get("PAPER_TEST_RSI_LOW", str(RSI_LOW)), "rsi-low"),
        "rsi_high": positive_float(os.environ.get("PAPER_TEST_RSI_HIGH", str(RSI_HIGH)), "rsi-high"),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    env_cfg = config_from_env()
    parser = argparse.ArgumentParser(description="Run live BTC/USDT paper RSI simulation on Binance klines.")
    parser.add_argument("--hours", type=lambda v: positive_float(v, "hours"), default=env_cfg["hours"])
    parser.add_argument("--symbol", type=parse_symbol, default=env_cfg["symbol"])
    parser.add_argument("--timeframe", type=parse_timeframe, default=env_cfg["timeframe"])
    parser.add_argument("--poll-seconds", type=lambda v: positive_float(v, "poll-seconds"), default=env_cfg["poll_seconds"])
    parser.add_argument("--start-usdt", type=lambda v: positive_float(v, "start-usdt"), default=env_cfg["start_usdt"])
    parser.add_argument("--rsi-period", type=lambda v: positive_int(v, "rsi-period"), default=env_cfg["rsi_period"])
    parser.add_argument("--rsi-low", type=lambda v: positive_float(v, "rsi-low"), default=env_cfg["rsi_low"])
    parser.add_argument("--rsi-high", type=lambda v: positive_float(v, "rsi-high"), default=env_cfg["rsi_high"])
    args = parser.parse_args(argv)
    if args.rsi_low >= args.rsi_high:
        parser.error("--rsi-low must be less than --rsi-high")
    return args


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

    def apply(self, price: float, r: float, rsi_low: float, rsi_high: float) -> None:
        if r <= rsi_low and self.usdt > 5.0:
            cost = self.usdt * 0.999
            self.btc += (cost * (1.0 - FEE)) / price
            self.usdt = 0.0
            self.trades += 1
        elif r >= rsi_high and self.btc > 0.0:
            gross = self.btc * price
            self.usdt = gross * (1.0 - FEE)
            self.btc = 0.0
            self.trades += 1


def main() -> None:
    args = parse_args()
    try:
        import ccxt
    except ImportError:
        raise ValueError("Missing dependency: pip install ccxt")
    ex = ccxt.binance({"enableRateLimit": True})
    end = time.time() + args.hours * 3600
    p = Paper(usdt=args.start_usdt)
    print(
        f"PAPER ({args.hours:g}h) | {args.symbol} {args.timeframe} | {args.start_usdt} USDT | "
        f"RSI({args.rsi_period}) buy<={args.rsi_low} sell>={args.rsi_high} (matches GCT) | Ctrl+C to stop"
    )
    while time.time() < end:
        try:
            ohlcv = ex.fetch_ohlcv(args.symbol, args.timeframe, limit=80)
        except Exception as e:
            print(f"fetch: {e}; sleep 10s")
            time.sleep(10)
            continue
        if not ohlcv:
            time.sleep(args.poll_seconds)
            continue
        ts, _, _, _, c, _ = ohlcv[-1]
        if p.last_candle_ms == ts:
            time.sleep(args.poll_seconds)
            continue
        p.last_candle_ms = int(ts)
        closes = [float(x[4]) for x in ohlcv]
        r = rsi_last(closes, args.rsi_period)
        if r is None:
            time.sleep(args.poll_seconds)
            continue
        price = float(c)
        p.apply(price, r, args.rsi_low, args.rsi_high)
        print(
            f"equity=${p.mark(price):,.2f} usdt={p.usdt:.2f} btc={p.btc:.6f} "
            f"RSI={r:.2f} trades={p.trades}"
        )
        time.sleep(args.poll_seconds)
    ohlcv = ex.fetch_ohlcv(args.symbol, args.timeframe, limit=1)
    px = float(ohlcv[-1][4]) if ohlcv else 0.0
    print(f"Done. Final ~${p.mark(px):,.2f} trades={p.trades}")


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2)
