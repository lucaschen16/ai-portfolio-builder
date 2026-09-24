"""
Technical Signal Engine

This file computes technical indicators from raw price data.
Everything here is pure Python math — no LLM, no API calls.

Your job is to complete all the helper functions and compute_signals().
"""

import math


# ── Helper 1: Simple Moving Average ─────────────────────────────────
#
# A moving average smooths out price data by averaging the last N days.
# Example: the 20-day MA is the average of the last 20 closing prices.
#
# If the price is above its moving average, it generally means the stock
# has been going up recently. If it's below, it's been going down.

def simple_moving_average(prices: list[float], window: int) -> list[float | None]:
    """
    TODO 2a: Calculate the simple moving average for each day.

    Returns a list the same length as prices.
    For the first (window - 1) days, return None (not enough data).
    For each day after that, return the average of the last `window` prices.
    """
    pass


# ── Helper 2: RSI (Relative Strength Index) ─────────────────────────
#
# RSI measures how fast a stock is going up or down on a scale of 0-100.
#
#   RSI > 70  → the stock might be "overbought" (gone up too fast)
#   RSI < 30  → the stock might be "oversold" (gone down too fast)
#   RSI 30-70 → somewhere in between

def compute_rsi(closes: list[float], period: int = 14) -> float | None:
    """
    TODO 2b: Calculate the RSI using the last `period` price changes.

    Returns a number between 0 and 100, or None if not enough data.
    Return None if len(closes) < period + 1.
    """
    pass


# ── Helper 3: Volatility ────────────────────────────────────────────
#
# Volatility measures how much the price jumps around day-to-day.
# A stock with high volatility has big swings up and down.
# A stock with low volatility moves slowly and steadily.
#
# We use "annualized" volatility: multiply daily vol by sqrt(252)
# because there are about 252 trading days in a year.

def compute_volatility(closes: list[float], window: int = 20) -> float | None:
    """
    TODO 2c: Calculate the 20-day annualized volatility as a percentage.

    Returns something like 28.5 meaning "28.5% annualized volatility".
    Returns None if not enough data (need at least window + 1 closes).
    """
    pass


# ── Helper 4: Support and Resistance ────────────────────────────────
#
# Support = a price level where the stock tends to stop falling
# Resistance = a price level where the stock tends to stop rising
#
# We find these by looking for "pivot" points — local highs and lows
# where the price reversed direction.

def find_support_resistance(highs: list[float], lows: list[float], window: int = 5) -> tuple[list[float], list[float]]:
    """
    TODO 2d: Find pivot highs and pivot lows in the price data.

    A pivot high is a point higher than all neighbors within `window` days.
    A pivot low is a point lower than all neighbors within `window` days.

    Returns (pivot_highs, pivot_lows) as two lists of price values.
    """
    pass


# ── Helper 5: Volume Analysis ───────────────────────────────────────
#
# Volume = how many shares were traded on a given day.
# High volume on an up day means lots of people are buying (strong move).
# High volume on a down day means lots of people are selling (strong move).
# Low volume means not many people care about the price move.

def compute_volume_signal(volumes: list[int]) -> dict:
    """
    TODO 2e: Compare today's volume to the 20-day average.

    Returns a dict with keys: avg_20, latest, ratio, signal.
    signal is "high" if ratio > 1.5, "low" if ratio < 0.6, else "normal".
    If fewer than 20 data points, return all None values with signal "unknown".
    """
    pass


# ── Main function: combine everything ────────────────────────────────

def compute_signals(ohlcv: dict) -> dict:
    """
    TODO 2f: Take raw OHLCV data and compute all technical signals.

    The ohlcv dict has these keys (from market_data.py):
      ohlcv["closes"]  — list of closing prices
      ohlcv["highs"]   — list of daily highs
      ohlcv["lows"]    — list of daily lows
      ohlcv["volumes"] — list of daily volumes
    """

    # ── Step A: Pull out the lists and get the current price ─────────
    #
    # closes = ohlcv["closes"]
    # highs  = ohlcv["highs"]
    # lows   = ohlcv["lows"]
    # current_price = closes[-1]      # the last item in the list

    # ── Step B: Trend ────────────────────────────────────────────────
    #
    # 1. ma20_series = simple_moving_average(closes, 20)
    # 2. ma50_series = simple_moving_average(closes, 50)
    # 3. ma20 = ma20_series[-1]       # last value in the MA20 list
    # 4. ma50 = ma50_series[-1]       # last value in the MA50 list
    #
    # 5. Compare the price to the moving averages:
    #      price_above_ma20 = current_price > ma20
    #      price_above_ma50 = current_price > ma50
    #      ma20_above_ma50  = ma20 > ma50
    #    (but if ma20 or ma50 is None, set the comparison to None too)
    #
    # 6. Decide the trend signal using if/elif/else:
    #      if price is above both and ma20 > ma50 → "bullish"
    #      elif price is below both               → "bearish"
    #      else                                   → "neutral"
    #
    # 7. Round the ma20_series and ma50_series for the chart.
    #    Use a simple loop:
    #      rounded_ma20 = []
    #      for value in ma20_series:
    #          if value is not None:
    #              rounded_ma20.append(round(value, 2))
    #          else:
    #              rounded_ma20.append(None)
    #    Do the same for ma50_series.

    # ── Step C: Momentum ─────────────────────────────────────────────
    #
    # 1. rsi = compute_rsi(closes)
    #
    # 2. Calculate the 1-month return (how much the price changed in ~21 days):
    #      if len(closes) >= 21:
    #          price_21_days_ago = closes[-21]
    #          one_month_return = ((current_price - price_21_days_ago) / price_21_days_ago) * 100
    #          one_month_return = round(one_month_return, 2)
    #      else:
    #          one_month_return = None
    #
    # 3. Decide the momentum signal:
    #      if rsi > 70              → "stretched"
    #      elif rsi < 30            → "weak"
    #      elif one_month_return > 5 and rsi > 50 → "supportive"
    #      else                     → "mixed"

    # ── Step D: Volatility ───────────────────────────────────────────
    #
    # 1. vol = compute_volatility(closes)
    #
    # 2. Decide the volatility signal:
    #      if vol is None           → "unknown"
    #      elif vol < 20            → "low"
    #      elif vol < 35            → "medium"
    #      else                     → "high"

    # ── Step E: Support and Resistance levels ────────────────────────
    #
    # 1. pivot_highs, pivot_lows = find_support_resistance(highs, lows)
    #
    # 2. Find the nearest support (the highest pivot low that is BELOW current_price).
    #    Use a simple loop:
    #
    #      supports = []
    #      for price in pivot_lows:
    #          if price < current_price:
    #              supports.append(price)
    #      supports.sort(reverse=True)      # biggest first
    #
    #      if len(supports) >= 1:
    #          nearest_support = round(supports[0], 2)
    #      else:
    #          nearest_support = None
    #
    #      if len(supports) >= 2:
    #          second_support = round(supports[1], 2)
    #      else:
    #          second_support = None
    #
    # 3. Find the nearest resistance (the lowest pivot high that is ABOVE current_price).
    #    Same idea:
    #
    #      resistances = []
    #      for price in pivot_highs:
    #          if price > current_price:
    #              resistances.append(price)
    #      resistances.sort()               # smallest first
    #
    #      if len(resistances) >= 1:
    #          nearest_resistance = round(resistances[0], 2)
    #      else:
    #          nearest_resistance = None
    #
    #      if len(resistances) >= 2:
    #          second_resistance = round(resistances[1], 2)
    #      else:
    #          second_resistance = None
    #
    # 4. Decide the levels signal.
    #    If we have both a support and a resistance:
    #      range_size = nearest_resistance - nearest_support
    #      position = (current_price - nearest_support) / range_size
    #      if position < 0.25  → "near_support"
    #      if position > 0.75  → "near_resistance"
    #      else                → "mid_range"
    #    If we only have resistance → "near_resistance"
    #    If we only have support    → "breakout_zone"
    #    If we have neither         → "mid_range"

    # ── Step F: Volume ───────────────────────────────────────────────
    #
    # volume = compute_volume_signal(ohlcv["volumes"])

    # ── Step G: Return everything ────────────────────────────────────
    #
    # Return a dictionary with this shape:
    # {
    #     "current_price": round(current_price, 2),
    #     "trend": {
    #         "ma20": round(ma20, 2),
    #         "ma50": round(ma50, 2),
    #         "ma20_series": rounded_ma20,
    #         "ma50_series": rounded_ma50,
    #         "price_above_ma20": price_above_ma20,
    #         "price_above_ma50": price_above_ma50,
    #         "ma20_above_ma50": ma20_above_ma50,
    #         "signal": trend_signal,
    #     },
    #     "momentum": {
    #         "rsi": rsi,
    #         "one_month_return": one_month_return,
    #         "signal": momentum_signal,
    #     },
    #     "volatility": {
    #         "realized_vol_20d": vol,
    #         "signal": vol_signal,
    #     },
    #     "levels": {
    #         "nearest_support": nearest_support,
    #         "second_support": second_support,
    #         "nearest_resistance": nearest_resistance,
    #         "second_resistance": second_resistance,
    #         "signal": levels_signal,
    #     },
    #     "volume": volume,
    # }

    pass
