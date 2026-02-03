# bot.py
# GoalFlowPulse Bot
# - Reads secrets from environment variables (set in GitHub Actions Secrets)
# - Posts live scores, major-league news, transfer news, transfer rumours
# - Responds to league-specific commands
# - Default mode: SCHEDULE (used by GitHub Actions). Optional POLLING mode for local testing.

import os
import requests
import time
from datetime import datetime, timedelta
from telegram import Bot, ParseMode
from telegram.ext import Updater, CommandHandler
import json
import hashlib

# -------------------------
# Configuration (do not hardcode secrets)
# -------------------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
CHANNEL_ID = "@GoalFlowPulse"  # your public channel username

# Local file used for simple dedupe cache (GitHub Actions workspace is ephemeral,
# but this helps avoid duplicates within a single run or quick re-runs)
CACHE_FILE = "posted_cache.json"
CACHE_TTL_HOURS = 24

# -------------------------
# League mapping for commands
# -------------------------
LEAGUE_COMMANDS = {
    "premierleague": "Premier League",
    "laliga": "La Liga",
    "bundesliga": "Bundesliga",
    "seriea": "Serie A",
    "ligue1": "Ligue 1",
    "ligaportugal": "Liga Portugal",
    "eredivisie": "Eredivisie",
    "belgian": "Belgian Pro League",
    "scottish": "Scottish Premiership",
    "superlig": "Süper Lig",
    "mls": "MLS",
    "ligamx": "Liga MX",
    "brasileirao": "Campeonato Brasileiro Série A",
    "argentina": "Argentine Primera División",
    "saudi": "Saudi Pro League",
    "jleague": "J1 League",
    "aleague": "A-League"
}

# -------------------------
# Helpers: cache, dedupe, send
# -------------------------
def load_cache():
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # remove old entries
            cutoff = datetime.utcnow() - timedelta(hours=CACHE_TTL_HOURS)
            cleaned = {k: v for k, v in data.items() if datetime.fromisoformat(v) > cutoff}
            return cleaned
    except Exception:
        pass
    return {}

def save_cache(cache):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f)
    except Exception:
        pass

def make_id(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def already_posted(text, cache):
    _id = make_id(text)
    return _id in cache

def mark_posted(text, cache):
    _id = make_id(text)
    cache[_id] = datetime.utcnow().isoformat()

def safe_send(text, disable_preview=False):
    bot = Bot(token=TELEGRAM_TOKEN)
    try:
        bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode=ParseMode.HTML, disable_web_page_preview=disable_preview)
        return True
    except Exception as e:
        print("Telegram send error:", e)
        return False

# -------------------------
# Fetching functions
# -------------------------
def fetch_live_scores():
    """
    Fetch matches from football-data.org and return formatted messages for IN_PLAY and FINISHED matches.
    """
    url = "https://api.football-data.org/v4/matches"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
        matches = data.get("matches", [])
        messages = []
        for m in matches:
            status = m.get("status")
            if status in ("IN_PLAY", "FINISHED"):
                home = m.get("homeTeam", {}).get("name", "Home")
                away = m.get("awayTeam", {}).get("name", "Away")
                score = m.get("score", {})
                ft = score.get("fullTime", {})
                h = ft.get("home")
                a = ft.get("away")
                # fallback to halfTime or placeholders
                if h is None:
                    h = score.get("halfTime", {}).get("home", "-")
                if a is None:
                    a = score.get("halfTime", {}).get("away", "-")
                tag = "⚽ LIVE UPDATE" if status == "IN_PLAY" else "✅ FINAL SCORE"
                # Add pidgin banter for live matches
                banter = ""
                if status == "IN_PLAY":
                    try:
                        h_int = int(h) if isinstance(h, int) or (isinstance(h, str) and h.isdigit()) else None
                        a_int = int(a) if isinstance(a, int) or (isinstance(a, str) and a.isdigit()) else None
                    except Exception:
                        h_int = a_int = None
                    if h_int is not None and a_int is not None:
                        if h_int > a_int:
                            banter = f"\n\nPidgin: {home} dey knack {away} {h_int}-{a_int} — who go stop dem?"
                        elif a_int > h_int:
                            banter = f"\n\nPidgin: {away} dey carry road {a_int}-{h_int} — e pain but na football!"
                        else:
                            banter = f"\n\nPidgin: {home} {h_int} - {a_int} {away} — balance game so far!"
                message = f"{tag}\n\n<b>{home}</b> {h} - {a} <b>{away}</b>{banter}\n\nPowered by GoalFlowPulse"
                messages.append(message)
        return messages
    except Exception as e:
        print("Error fetching live scores:", e)
        return []

def fetch_news_for_query(query, max_items=3):
    """
    Generic NewsAPI fetcher. Returns list of formatted strings.
    """
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "pageSize": max_items,
        "sortBy": "publishedAt",
        "apiKey": NEWS_API_KEY
    }
    try:
        r = requests.get(url, params=params, timeout=12)
        r.raise_for_status()
        data = r.json()
        articles = data.get("articles", [])
        items = []
        for a in articles:
            title = a.get("title", "No title")
            src = a.get("source", {}).get("name", "Unknown")
            url = a.get("url", "")
            items.append(f"📰 {query}\n<b>{title}</b>\nSource: {src}\n{url}")
        return items
    except Exception as e:
        print(f"News fetch error for '{query}':", e)
        return [f"Error fetching news for {query}: {e}"]

def fetch_major_league_news(max_per_league=1, top_limit=6):
    """
    Fetch top items for each major league and return a deduped top list.
    """
    queries = [
        "Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1",
        "Liga Portugal", "Eredivisie", "Belgian Pro League", "Scottish Premiership", "Süper Lig",
        "MLS", "Liga MX", "Campeonato Brasileiro Série A", "Argentine Primera División",
        "Saudi Pro League", "J1 League", "A-League"
    ]
    collected = []
    for q in queries:
        items = fetch_news_for_query(q, max_items=max_per_league)
        collected.extend(items)
    # dedupe by title line
    seen = set()
    final = []
    for m in collected:
        key = m.split("\n", 1)[1] if "\n" in m else m
        if key not in seen:
            seen.add(key)
            final.append(m)
        if len(final) >= top_limit:
            break
    return final

# -------------------------
# Transfer news vs rumours
# -------------------------
def fetch_transfer_news(max_items=3):
    """
    Attempt to fetch confirmed transfer news. Prioritize keywords that indicate confirmation.
    """
    queries = [
        '"official" transfer', '"confirms" transfer', '"signed" "official"', '"joins" "official"',
        '"announces signing"', '"completed transfer"', '"contract signed"'
    ]
    messages = []
    for q in queries:
        items = fetch_news_for_query(q, max_items=1)
        for it in items:
            # simple heuristic: if title contains 'official' or 'confirms' mark as confirmed
            if "official" in it.lower() or "confirms" in it.lower() or "signed" in it.lower():
                messages.append("[CONFIRMED] " + it)
            else:
                messages.append("[POSSIBLE] " + it)
    # dedupe and limit
    seen = set()
    final = []
    for m in messages:
        key = m.split("\n", 1)[1] if "\n" in m else m
        if key not in seen:
            seen.add(key)
            final.append(m)
        if len(final) >= max_items:
            break
    return final

def fetch_transfer_rumours(max_items=5):
    """
    Fetch transfer rumours. Label clearly as RUMOUR.
    """
    queries = [
        "transfer rumour", "transfer rumours", "linked with", "sources say transfer",
        "Fabrizio Romano transfer", "transfer update", "transfer interest"
    ]
    messages = []
    for q in queries:
        items = fetch_news_for_query(q, max_items=1)
        for it in items:
            messages.append("[RUMOUR] " + it)
    # dedupe and limit
    seen = set()
    final = []
    for m in messages:
        key = m.split("\n", 1)[1] if "\n" in m else m
        if key not in seen:
            seen.add(key)
            final.append(m)
        if len(final) >= max_items:
            break
    return final

# -------------------------
# Telegram command handlers (for POLLING mode)
# -------------------------
def start_handler(update, context):
    text = ("Welcome to GoalFlowPulse ⚡\n"
            "Commands: /premierleague /laliga /bundesliga /seriea /ligue1\n"
            "Transfer commands: /transfernews /transferrumours /transfers\n"
            "Channel posts: live scores every 15 minutes; news & transfer news at 08:30 & 20:30 local.")
    update.message.reply_text(text)

def league_handler(update, context):
    cmd = update.message.text.lstrip("/").lower()
    league = LEAGUE_COMMANDS.get(cmd)
    if not league:
        update.message.reply_text("League not recognized.")
        return
    items = fetch_news_for_query(league, max_items=3)
    for it in items:
        update.message.reply_text(it, disable_web_page_preview=True)

def transfernews_handler(update, context):
    items = fetch_transfer_news(max_items=3)
    for it in items:
        update.message.reply_text(it, disable_web_page_preview=True)

def transferrumours_handler(update, context):
    items = fetch_transfer_rumours(max_items=5)
    for it in items:
        update.message.reply_text(it, disable_web_page_preview=True)

def transfers_handler(update, context):
    update.message.reply_text("Latest confirmed transfers:")
    for it in fetch_transfer_news(3):
        update.message.reply_text(it, disable_web_page_preview=True)
    update.message.reply_text("Latest rumours:")
    for it in fetch_transfer_rumours(3):
        update.message.reply_text(it, disable_web_page_preview=True)

# -------------------------
# Scheduled runner (used by GitHub Actions)
# -------------------------
def run_scheduled_tasks():
    """
    Decide what to post based on current UTC time.
    GitHub Actions cron should trigger this script at:
      - every 15 minutes (for scores)
      - 07:30 UTC and 19:30 UTC (for news & transfer news -> corresponds to 08:30 and 20:30 Nigeria)
      - optionally every 2 hours for rumours during transfer windows (workflow can schedule that)
    This function checks current UTC time and posts accordingly.
    """
    cache = load_cache()

    now = datetime.utcnow()
    hour = now.hour
    minute = now.minute

    # 1) Live scores: post when minute % 15 == 0 (workflow runs every 15 minutes)
    if minute % 15 == 0:
        scores = fetch_live_scores()
        for s in scores:
            if not already_posted(s, cache):
                if safe_send(s):
                    mark_posted(s, cache)

    # 2) Major-league news & transfer news: post at 07:30 UTC and 19:30 UTC
    if (hour == 7 and minute == 30) or (hour == 19 and minute == 30):
        news_items = fetch_major_league_news(max_per_league=1, top_limit=6)
        for n in news_items:
            if not already_posted(n, cache):
                if safe_send(n, disable_preview=False):
                    mark_posted(n, cache)
        # Transfer news (confirmed)
        tnews = fetch_transfer_news(max_items=4)
        for t in tnews:
            if not already_posted(t, cache):
                if safe_send(t, disable_preview=False):
                    mark_posted(t, cache)

    # 3) Transfer rumours: post on the hour every 2 hours (workflow can schedule every 2 hours)
    # Here we check minute == 0 and hour % 2 == 0 as a safety check
    if minute == 0 and (hour % 2 == 0):
        rumours = fetch_transfer_rumours(max_items=5)
        for r in rumours:
            if not already_posted(r, cache):
                # clearly label as rumour in message body already
                if safe_send(r, disable_preview=False):
                    mark_posted(r, cache)

    save_cache(cache)

# -------------------------
# Entrypoint
# -------------------------
if __name__ == "__main__":
    # Mode selection:
    # - Set RUN_MODE=POLLING to run as a long-running bot locally (for testing)
    # - Default is SCHEDULE: run once and exit (used by GitHub Actions)
    run_mode = os.getenv("RUN_MODE", "SCHEDULE").upper()

    if run_mode == "POLLING":
        # Start polling bot for commands (useful for local testing or a VPS)
        updater = Updater(TELEGRAM_TOKEN, use_context=True)
        dp = updater.dispatcher
        dp.add_handler(CommandHandler("start", start_handler))
        for cmd in LEAGUE_COMMANDS.keys():
            dp.add_handler(CommandHandler(cmd, league_handler))
        dp.add_handler(CommandHandler("transfernews", transfernews_handler))
        dp.add_handler(CommandHandler("transferrumours", transferrumours_handler))
        dp.add_handler(CommandHandler("transfers", transfers_handler))
        print("Starting polling mode. Press Ctrl+C to stop.")
        updater.start_polling()
        updater.idle()
    else:
        # Scheduled run: perform tasks based on UTC time and exit
        run_scheduled_tasks()
