# news_fetcher.py
import requests
import feedparser
from db_utils import already_posted, mark_posted

RSS_SOURCES = [
    "https://www.skysports.com/rss/12040",
    "https://www.espn.com/espn/rss/football/news",
    "https://www.goal.com/en/feeds/news",
    "https://feeds.bbci.co.uk/sport/football/rss.xml"
]

def fetch_rss_headlines(limit=12):
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
    seen = set()
    deduped = []
    for it in items:
        if it["title"] not in seen:
            deduped.append(it)
            seen.add(it["title"])
    return deduped

def fetch_newsapi_headlines(api_key: str, query="football OR transfer OR transfer rumour", limit=8):
    url = "https://newsapi.org/v2/everything"
    params = {"q": query, "language": "en", "pageSize": limit, "sortBy": "publishedAt", "apiKey": api_key}
    try:
        r = requests.get(url, params=params, timeout=10).json()
        articles = r.get("articles", [])
        return [{"title": a["title"], "link": a["url"], "source": a["source"]["name"], "published": a["publishedAt"]} for a in articles]
    except Exception:
        return []

def get_top_news(newsapi_key=None, max_items=6):
    headlines = fetch_rss_headlines(limit=12)
    if len(headlines) < max_items and newsapi_key:
        more = fetch_newsapi_headlines(newsapi_key, limit=12)
        titles = {h["title"] for h in headlines}
        for m in more:
            if m["title"] not in titles:
                headlines.append(m)
                titles.add(m["title"])
    return headlines[:max_items]

def get_top_news_unique(newsapi_key=None, max_items=6):
    candidates = get_top_news(newsapi_key, max_items*2)
    unique = []
    for item in candidates:
        title = (item.get("title") or "").strip()
        url = (item.get("link") or "").strip()
        if not title and not url:
            continue
        if already_posted(title, url):
            continue
        unique.append(item)
        if len(unique) >= max_items:
            break
    return unique

def mark_news_as_posted(items):
    for it in items:
        title = (it.get("title") or "").strip()
        url = (it.get("link") or "").strip()
        if title or url:
            mark_posted(title, url)