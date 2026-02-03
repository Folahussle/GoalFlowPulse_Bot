# bot.py
import os
import requests
from datetime import datetime
from telegram import Bot, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram.update import Update

# Load secrets from environment (set in GitHub Actions / local env)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")

CHANNEL_ID = "@GoalFlowPulse"  # your channel username

# Leagues mapping for commands
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

bot = Bot(token=TELEGRAM_TOKEN)

def send_to_channel(text: str):
    try:
        bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode=ParseMode.HTML)
    except Exception as e:
        print("Telegram send error:", e)

# ---------- Scores ----------
def fetch_live_scores():
    url = "https://api.football-data.org/v4/matches"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        data = r.json()
        matches = data.get("matches", [])
        messages = []
        for m in matches:
            status = m.get("status")
            if status in ("IN_PLAY", "FINISHED"):
                home = m["homeTeam"]["name"]
                away = m["awayTeam"]["name"]
                ft = m["score"].get("fullTime", {})
                h = ft.get("home") if ft else None
                a = ft.get("away") if ft else None
                score_text = f"{h if h is not None else '-'} - {a if a is not None else '-'}"
                tag = "⚽ LIVE" if status == "IN_PLAY" else "✅ FINAL"
                messages.append(f"{tag}\n<b>{home}</b> {score_text} <b>{away}</b>\nPowered by GoalFlowPulse")
        return messages
    except Exception as e:
        print("Scores fetch error:", e)
        return []

# ---------- News (filtered by leagues) ----------
def fetch_news_for_query(query, max_items=3):
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "pageSize": max_items,
        "sortBy": "publishedAt",
        "apiKey": NEWS_API_KEY
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        articles = data.get("articles", [])
        items = []
        for a in articles:
            title = a.get("title")
            src = a.get("source", {}).get("name")
            url = a.get("url")
            items.append(f"📰 <b>{query}</b>\n{title}\nSource: {src}\n{url}")
        return items
    except Exception as e:
        print("News fetch error:", e)
        return [f"Error fetching news for {query}: {e}"]

def fetch_major_league_news():
    # Build a combined query of major leagues (OR)
    queries = [
        "Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1",
        "Liga Portugal", "Eredivisie", "Belgian Pro League", "Scottish Premiership", "Süper Lig",
        "MLS", "Liga MX", "Campeonato Brasileiro Série A", "Argentine Primera División",
        "Saudi Pro League", "J1 League", "A-League"
    ]
    # Fetch top 3 articles per league and return flattened list
    messages = []
    for q in queries:
        items = fetch_news_for_query(q, max_items=1)
        messages.extend(items)
    # Keep top 6 overall (dedupe by title)
    seen = set()
    final = []
    for m in messages:
        t = m.split("\n",1)[0]
        if t not in seen:
            seen.add(t)
            final.append(m)
        if len(final) >= 6:
            break
    return final

# ---------- Transfer rumours (use news queries + RSS sources) ----------
def fetch_transfer_rumours():
    # Query keywords often used in transfer news
    queries = ["transfer", "transfer news", "Fabrizio Romano", "transfermarkt", "transfer rumours", "deadline day"]
    messages = []
    for q in queries:
        items = fetch_news_for_query(q, max_items=1)
        messages.extend(items)
    # Return top 4 unique
    seen = set()
    final = []
    for m in messages:
        if m not in seen:
            seen.add(m)
            final.append(m)
        if len(final) >= 4:
            break
    return final

# ---------- Pidgin / Nigerian flavor helper ----------
def pidgin_banter(home, away, home_score, away_score, status):
    # Simple examples; you can expand phrases
    if status == "IN_PLAY":
        if home_score > away_score:
            return f"{home} dey knack {away} {home_score}-{away_score} — who go stop dem? #NaijaBanter"
        elif away_score > home_score:
            return f"{away} dey carry road {away_score}-{home_score} — e pain but na football!"
        else:
            return f"{home} {home_score} - {away_score} {away} — balance game so far!"
    else:
        return f"Final: {home} {home_score} - {away_score} {away} — who dey celebrate?"

# ---------- Command handlers for Telegram ----------
def league_command(update: Update, context: CallbackContext):
    cmd = update.message.text.lstrip("/").lower()
    league = LEAGUE_COMMANDS.get(cmd)
    if not league:
        update.message.reply_text("League not found.")
        return
    items = fetch_news_for_query(league, max_items=3)
    for it in items:
        update.message.reply_text(it, disable_web_page_preview=True)

def start_command(update: Update, context: CallbackContext):
    text = ("Welcome to GoalFlowPulse ⚡\n"
            "Use commands like /premierleague /laliga /bundesliga to get league news.\n"
            "Channel posts: live scores every 15 minutes, news 08:30 & 20:30 daily.")
    update.message.reply_text(text)

# ---------- Scheduled runner (used by GitHub Actions) ----------
def run_scheduled_job():
    now = datetime.utcnow()  # GitHub Actions uses UTC; workflow will run at desired UTC times
    hour = now.hour
    minute = now.minute

    # Scores job (called every 15 minutes by workflow)
    scores = fetch_live_scores()
    for s in scores:
        send_to_channel(s)

    # News jobs: workflow will trigger at 07:30 UTC and 19:30 UTC for Nigeria 08:30/20:30 local
    # But we also allow workflow_dispatch to run this script and it will post based on env flag
    # For safety, we rely on workflow schedule to call the script at the right times.

# ---------- Main entry for local/manual run ----------
if __name__ == "__main__":
    # If running as a long‑running bot (local), start polling for commands
    mode = os.getenv("RUN_MODE", "SCHEDULE")  # SCHEDULE or POLLING
    if mode == "POLLING":
        updater = Updater(TELEGRAM_TOKEN, use_context=True)
        dp = updater.dispatcher
        dp.add_handler(CommandHandler("start", start_command))
        for cmd in LEAGUE_COMMANDS.keys():
            dp.add_handler(CommandHandler(cmd, league_command))
        updater.start_polling()
        updater.idle()
    else:
        # Scheduled run (GitHub Actions): run scheduled job
        # We will post scores and rely on workflow schedule for news times
        run_scheduled_job()