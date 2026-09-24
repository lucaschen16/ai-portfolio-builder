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
    """
    TODO 1: Fetch 1 year of daily OHLCV data for a ticker from Yahoo Finance.

    Steps:
    1. Build the URL using CHART_URL.format(ticker=ticker)
    2. Create a request with urllib.request.Request(url, headers=HEADERS)
    3. Open it with urllib.request.urlopen(request, timeout=15)
    4. Parse the JSON response with json.load(response)
    5. Get the chart result: payload["chart"]["result"][0]
    6. Extract timestamps: chart["timestamp"]
    7. Extract quote data: chart["indicators"]["quote"][0]
       This dict has keys: "open", "high", "low", "close", "volume"
    8. Loop through all the data points. For each row:
       - if any of open/high/low/close is None, skip that row
       - otherwise, round the OHLC values to 2 decimal places
       - convert volume to int (use 0 if volume is None)
    9. If you end up with fewer than 20 clean data points, return None
    10. Return a dict with keys:
        {
            "ticker": ticker,
            "timestamps": [...],
            "opens": [...],
            "highs": [...],
            "lows": [...],
            "closes": [...],
            "volumes": [...]
        }
    11. If anything fails (network error, bad response), return None

    Hint: wrap the whole thing in a try/except and return None on error.
    """
    pass


# ── Class 2 compatibility (fully implemented) ───────────────────────

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
