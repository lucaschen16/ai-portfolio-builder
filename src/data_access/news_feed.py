import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

HEADERS = {"User-Agent": "Mozilla/5.0"}


def _news_url(question: str, topic: str) -> str:
    query = " ".join((question or "").replace("?", " ").split())
    if not query:
        query = "stock market"

    if topic == "stock":
        query += " stock market"
    elif topic == "crypto":
        query += " crypto market"
    elif topic == "etf":
        query += " etf investing"
    else:
        query += " investing"
    return f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"


def get_news(question: str, topic: str, limit=6):
    try:
        request = urllib.request.Request(_news_url(question, topic), headers=HEADERS)
        with urllib.request.urlopen(request, timeout=15) as response:
            xml_data = response.read()
        feed = ET.fromstring(xml_data)
    except Exception:
        return []

    articles = []
    for item in feed.findall("./channel/item")[:limit]:
        articles.append({
            "title": item.findtext("title", default=""),
            "link": item.findtext("link", default=""),
            "published": item.findtext("pubDate", default=""),
            "source": item.findtext("source", default="Google News"),
        })
    return articles
