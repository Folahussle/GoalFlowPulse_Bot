# news_fetcher.py (excerpt)
from db_utils import already_posted, mark_posted
# ... existing imports and functions ...

def get_top_news_unique(newsapi_key=None, max_items=6):
    # Fetch candidates (RSS first, then NewsAPI fallback)
    candidates = get_top_news(newsapi_key)  # reuse existing function that returns list of dicts
    unique = []
    for item in candidates:
        title = item.get("title", "").strip()
        url = item.get("link", "").strip()
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
        title = it.get("title", "").strip()
        url = it.get("link", "").strip()
        if title or url:
            mark_posted(title, url)