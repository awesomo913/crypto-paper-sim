from __future__ import annotations


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
    avg_g = gains / period
    avg_l = losses / period
    if avg_l == 0:
        return 100.0
    rs = avg_g / avg_l
    return 100.0 - (100.0 / (1.0 + rs))


def buy_all(
    *,
    usdt: float,
    btc: float,
    price: float,
    fee: float,
    reserve: float = 1.0,
) -> tuple[float, float]:
    spend = usdt * reserve
    btc += (spend * (1.0 - fee)) / price
    return 0.0, btc


def sell_all(*, usdt: float, btc: float, price: float, fee: float) -> tuple[float, float]:
    gross = btc * price
    usdt = gross * (1.0 - fee)
    return usdt, 0.0


def buy_spend(*, usdt: float, btc: float, price: float, fee: float, spend: float) -> tuple[float, float]:
    btc += (spend * (1.0 - fee)) / price
    usdt -= spend
    return usdt, btc

