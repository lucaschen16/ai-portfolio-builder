import json
import re
import urllib.request

HEADERS = {"User-Agent": "Mozilla/5.0"}

# 1 year of daily OHLCV data from Yahoo Finance
CHART_URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    "?interval=1d&range=1y"
)

PRICE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=5d"

# Quick lookup for common names -> symbols
NAME_TO_TICKER = {
    "nvidia": "NVDA", "apple": "AAPL", "microsoft": "MSFT",
    "amazon": "AMZN", "tesla": "TSLA", "meta": "META",
    "alphabet": "GOOGL", "google": "GOOGL",
    "bitcoin": "BTC-USD", "ethereum": "ETH-USD", "solana": "SOL-USD",
}

IGNORE_SYMBOLS = {"ETF", "STOCK", "CRYPTO"}


def normalize_ticker(raw: str) -> str:
    """Turn user input like 'apple' or 'aapl' into a Yahoo Finance symbol."""
    cleaned = raw.strip()
    lowered = cleaned.lower()
    if lowered in NAME_TO_TICKER:
        return NAME_TO_TICKER[lowered]
    return cleaned.upper()


def fetch_ohlcv(ticker: str) -> dict | None:
    """Fetch one year of daily prices and volume, requiring at least 20 complete days."""
    try:
        request = urllib.request.Request(CHART_URL.format(ticker=ticker), headers=HEADERS)
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.load(response)

        chart = payload["chart"]["result"][0]
        quote = chart["indicators"]["quote"][0]
        data = {
            "ticker": ticker,
            "timestamps": [],
            "opens": [],
            "highs": [],
            "lows": [],
            "closes": [],
            "volumes": [],
        }
        rows = zip(
            chart["timestamp"], quote["open"], quote["high"], quote["low"],
            quote["close"], quote["volume"], strict=True,
        )
        for timestamp, opening, high, low, close, volume in rows:
            if None in (opening, high, low, close):
                continue
            data["timestamps"].append(timestamp)
            data["opens"].append(round(opening, 2))
            data["highs"].append(round(high, 2))
            data["lows"].append(round(low, 2))
            data["closes"].append(round(close, 2))
            data["volumes"].append(int(volume) if volume is not None else 0)

        return data if len(data["closes"]) >= 20 else None
    except Exception:
        return None


def _guess_ticker(question: str, topic: str) -> str | None:
    lowered = question.lower()
    for name, ticker in NAME_TO_TICKER.items():
        if name in lowered:
            return ticker
    if topic == "etf":
        return "SPY"
    if topic == "crypto":
        return "BTC-USD"
    matches = re.findall(r"\b[A-Z]{2,5}(?:-USD)?\b", question)
    if matches:
        for match in matches:
            if match not in IGNORE_SYMBOLS:
                return match
    return None


def get_market_snapshot(question: str, topic: str) -> dict | None:
    """Used by the Class 2 news explainer agent."""
    ticker = _guess_ticker(question, topic)
    if not ticker:
        return None
    try:
        req = urllib.request.Request(PRICE_URL.format(ticker=ticker), headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.load(resp)
    except Exception:
        return None

    result = payload["chart"]["result"][0]
    closes = result["indicators"]["quote"][0]["close"]
    closes = [float(c) for c in closes if c is not None]
    if len(closes) < 2:
        return None

    current = closes[-1]
    previous = closes[-2]
    change_pct = ((current - previous) / previous) * 100
    five_day_pct = ((current - closes[0]) / closes[0]) * 100

    return {
        "ticker": ticker,
        "price": round(current, 2),
        "daily_change_pct": round(change_pct, 2),
        "five_day_change_pct": round(five_day_pct, 2),
    }
