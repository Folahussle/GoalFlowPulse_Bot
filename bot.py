import os
import requests
import time
from datetime import datetime, timedelta
from telegram import Bot, ParseMode
import json
import hashlib

# --- Configuration (Set these in GitHub Secrets) ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
CHANNEL_ID = "@GoalFlowPulse"
CACHE_FILE = "posted_cache.json"

# --- The Expert Hierarchy ---
LEAGUE_HIERARCHY = {
    "CONTINENTAL": ["UEFA Champions League", "Europa League", "Conference League"],
    "BIG_FIVE": ["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"],
    "GLOBAL_MAJOR": ["MLS", "Saudi Pro League"],
    "LOWER_DIV": ["English Championship"]
}

def load_cache():
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except: pass
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f)

def safe_send(text):
    bot = Bot(token=TELEGRAM_TOKEN)
    try:
        bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode=ParseMode.HTML)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def get_nigerian_intro(category):
    intros = {
        "CONFIRMED": ["Omo, e don set!", "Correct gist:", "Official yarn:"],
        "RUMOUR": ["Gist dey fly say...", "Hear-say don start:", "Dem say..."],
        "SCORES": ["Update don land!", "See how market be:", "Final results don show:"]
    }
    import random
    return random.choice(intros.get(category, ["Abeg check this out:"]))

def fetch_news(query, max_items=2):
    url = f"https://newsapi.org/v2/everything?q={query}&language=en&pageSize={max_items}&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        articles = r.json().get("articles", [])
        return articles
    except: return []

def run_scheduled_tasks():
    cache = load_cache()
    now = datetime.utcnow()
    hour = now.hour
    minute = now.minute

    # 1. LIVE SCORES (Every 15 mins)
    if minute % 15 == 0:
        # Focusing on hierarchy: Continental and Big Five
        major_queries = LEAGUE_HIERARCHY["CONTINENTAL"] + LEAGUE_HIERARCHY["BIG_FIVE"]
        # Logic to fetch scores from football-data.org matches endpoint...
        # (Using existing logic from your current script but focusing on these IDs)

    # 2. MORNING/EVENING NEWS (07:30 & 19:30 UTC is 08:30 & 20:30 Nigeria)
    if (hour == 7 and minute == 30) or (hour == 19 and minute == 30):
        # Post Transfer News
        intro = get_nigerian_intro("CONFIRMED")
        t_news = fetch_news("transfer official confirmed", 3)
        for art in t_news:
            msg = f"<b>{intro}</b>\n\n⚽ {art['title']}\n\nRead more: {art['url']}"
            safe_send(msg)

        # Post League News via Hierarchy
        for cat, leagues in LEAGUE_HIERARCHY.items():
            for league in leagues[:2]: # Top 2 from each for brevity
                news = fetch_news(league, 1)
                for n in news:
                    safe_send(f"🏆 <b>{league} Update</b>\n\n{n['title']}\n{n['url']}")

if __name__ == "__main__":
    run_scheduled_tasks()
