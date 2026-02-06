# news_fetcher.py
import requests
import feedparser
from datetime import datetime, timedelta

# RSS sources to scrape (free)
RSS_SOURCES = [
    "https://www.skysports.com/rss/12040",  # Sky Sports Football
    "https://www.espn.com/espn/rss/football/news",
    "https://www.goal.com/en/feeds/news",
    "https://www.bbc.co.uk/sport/football/rss.xml"
]

def fetch_rss_headlines(limit=6):
    items = []
    for url in RSS_SOURCES:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:limit]:
                title = entry.get("title")
                link = entry.get("link")
                published = entry.get("published", "")
                items.append({"title": title, "link": link, "source": url, "published": published})
        except Exception:
            continue
    # dedupe by title
    seen = set()
    deduped = []
    for it in items:
        if it["title"] not in seen:
            deduped.append(it)
            seen.add(it["title"])
    return deduped[:limit]

def fetch_newsapi_headlines(api_key, query="football OR transfer OR transfer rumour", limit=6):
    url = "https://newsapi.org/v2/everything"
    params = {"q": query, "language": "en", "pageSize": limit, "sortBy": "publishedAt", "apiKey": api_key}
    try:
        r = requests.get(url, params=params, timeout=10).json()
        articles = r.get("articles", [])
        return [{"title": a["title"], "link": a["url"], "source": a["source"]["name"], "published": a["publishedAt"]} for a in articles]
    except Exception:
        return []

def get_top_news(newsapi_key=None):
    # Try RSS first (free). If not enough items and NewsAPI key provided, use NewsAPI.
    headlines = fetch_rss_headlines(limit=8)
    if len(headlines) < 4 and newsapi_key:
        more = fetch_newsapi_headlines(newsapi_key, limit=8)
        # merge and dedupe
        titles = {h["title"] for h in headlines}
        for m in more:
            if m["title"] not in titles:
                headlines.append(m)
                titles.add(m["title"])
    return headlines[:6]