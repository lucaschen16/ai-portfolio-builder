"""Compute technical indicators from daily prices and volume."""

from math import sqrt
from statistics import fmean, stdev


def simple_moving_average(prices: list[float], window: int) -> list[float | None]:
    if window < 1:
        raise ValueError("window must be positive")
    return [
        fmean(prices[end - window:end]) if end >= window else None
        for end in range(1, len(prices) + 1)
    ]


def compute_rsi(closes: list[float], period: int = 14) -> float | None:
    if period < 1 or len(closes) <= period:
        return None
    changes = [b - a for a, b in zip(closes[-period-1:-1], closes[-period:])]
    gains = sum(max(change, 0) for change in changes)
    losses = sum(max(-change, 0) for change in changes)
    return round(100 * gains / (gains + losses), 2) if gains + losses else 50.0


def compute_volatility(closes: list[float], window: int = 20) -> float | None:
    if window < 2 or len(closes) <= window:
        return None
    previous = closes[-window-1:-1]
    if 0 in previous:
        return None
    returns = [b / a - 1 for a, b in zip(previous, closes[-window:])]
    return round(stdev(returns) * sqrt(252) * 100, 2)


def find_support_resistance(highs: list[float], lows: list[float], window: int = 5) -> tuple[list[float], list[float]]:
    pivot_highs, pivot_lows = [], []
    for i in range(window, len(highs) - window):
        if highs[i] > max(highs[i-window:i] + highs[i+1:i+window+1]):
            pivot_highs.append(highs[i])
        if lows[i] < min(lows[i-window:i] + lows[i+1:i+window+1]):
            pivot_lows.append(lows[i])
    return pivot_highs, pivot_lows


def compute_volume_signal(volumes: list[int]) -> dict:
    if len(volumes) < 20:
        return dict(avg_20=None, latest=None, ratio=None, signal="unknown")
    average = fmean(volumes[-20:])
    ratio = volumes[-1] / average if average else None
    signal = "unknown"
    if ratio is not None:
        signal = "high" if ratio > 1.5 else "low" if ratio < 0.6 else "normal"
    return dict(avg_20=average, latest=volumes[-1], ratio=round(ratio, 2) if ratio is not None else None, signal=signal)


def _levels(ohlcv, price):
    highs, lows = find_support_resistance(ohlcv["highs"], ohlcv["lows"])
    supports = sorted({low for low in lows if low < price}, reverse=True)
    resistances = sorted({high for high in highs if high > price})
    support, second_support = (supports + [None, None])[:2]
    resistance, second_resistance = (resistances + [None, None])[:2]
    signal = "mid_range"
    if support is not None and resistance is not None:
        position = (price - support) / (resistance - support)
        if position < 0.25:
            signal = "near_support"
        elif position > 0.75:
            signal = "near_resistance"
    elif resistance is not None:
        signal = "near_resistance"
    elif support is not None:
        signal = "breakout_zone"
    return dict(nearest_support=support, second_support=second_support,
                nearest_resistance=resistance, second_resistance=second_resistance, signal=signal)


def compute_signals(ohlcv: dict) -> dict:
    closes = ohlcv["closes"]
    if not closes:
        return {}
    price = closes[-1]
    ma20_series = simple_moving_average(closes, 20)
    ma50_series = simple_moving_average(closes, 50)
    ma20, ma50 = ma20_series[-1], ma50_series[-1]
    trend = "neutral"
    if ma20 is not None and ma50 is not None:
        if price > ma20 > ma50:
            trend = "bullish"
        elif price < min(ma20, ma50):
            trend = "bearish"

    rsi = compute_rsi(closes)
    monthly = None
    if len(closes) >= 21 and closes[-21]:
        monthly = round((price / closes[-21] - 1) * 100, 2)
    momentum = "mixed"
    if rsi is not None:
        if rsi > 70:
            momentum = "stretched"
        elif rsi < 30:
            momentum = "weak"
        elif rsi > 50 and monthly is not None and monthly > 5:
            momentum = "supportive"

    vol = compute_volatility(closes)
    vol_signal = "unknown"
    if vol is not None:
        vol_signal = "low" if vol < 20 else "medium" if vol < 35 else "high"

    def rounded(value):
        return round(value, 2) if value is not None else None

    return {
        "current_price": rounded(price),
        "trend": {
            "ma20": rounded(ma20), "ma50": rounded(ma50),
            "ma20_series": [rounded(value) for value in ma20_series],
            "ma50_series": [rounded(value) for value in ma50_series],
            "price_above_ma20": price > ma20 if ma20 is not None else None,
            "price_above_ma50": price > ma50 if ma50 is not None else None,
            "ma20_above_ma50": ma20 > ma50 if ma50 is not None else None,
            "signal": trend,
        },
        "momentum": dict(rsi=rsi, one_month_return=monthly, signal=momentum),
        "volatility": dict(realized_vol_20d=vol, signal=vol_signal),
        "levels": _levels(ohlcv, price),
        "volume": compute_volume_signal(ohlcv["volumes"]),
    }
