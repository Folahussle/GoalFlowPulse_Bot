# bot.py
import os
import requests
import time
from utils import format_score_message, LEAGUE_HIERARCHY, nigeria_vibe
from news_fetcher import get_top_news

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # e.g., @GoalFlowPulse
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")  # optional

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def send_telegram(text, parse_mode=None):
    data = {"chat_id": CHANNEL_ID, "text": text}
    if parse_mode:
        data["parse_mode"] = parse_mode
    try:
        r = requests.post(f"{TELEGRAM_API}/sendMessage", data=data, timeout=10)
        return r.ok
    except Exception as e:
        print("Telegram send error:", e)
        return False

def post_live_scores():
    # Football-Data.org endpoint for matches
    url = "https://api.football-data.org/v4/matches"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        matches = data.get("matches", [])
        # Filter for major leagues and live/finished
        major_competitions = set(LEAGUE_HIERARCHY["continental"] + LEAGUE_HIERARCHY["top_flights"])
        posted = 0
        for m in matches:
            status = m.get("status")
            comp = m.get("competition", {}).get("name", "")
            # Post only if competition in our major list and status is IN_PLAY or FINISHED
            if comp in major_competitions and status in ["IN_PLAY", "FINISHED"]:
                text = format_score_message(m, CHANNEL_ID)
                send_telegram(text)
                posted += 1
                # avoid spamming: small pause
                time.sleep(1)
        if posted == 0:
            send_telegram(nigeria_vibe("No live or finished matches right now for the major leagues."))
    except Exception as e:
        print("Error fetching live scores:", e)
        send_telegram(nigeria_vibe("Error fetching live scores. I go check and come back."))

def post_daily_news():
    headlines = get_top_news(NEWSAPI_KEY)
    if not headlines:
        send_telegram(nigeria_vibe("No news found right now. Try again later."))
        return
    text_lines = ["🔥 Top Football News & Transfer Rumours 🔥\n"]
    for h in headlines[:6]:
        title = h.get("title")
        link = h.get("link")
        source = h.get("source", h.get("source", "news"))
        text_lines.append(f"• {title} — {source}\n{link}\n")
    text_lines.append(f"\nFollow {CHANNEL_ID} for live scores and more.")
    send_telegram("\n".join(text_lines))

def handle_command(command):
    # Minimal command handler for manual runs via workflow_dispatch or future webhook
    cmd = command.strip().lower()
    if cmd == "livescores":
        post_live_scores()
    elif cmd == "news":
        post_daily_news()
    elif cmd == "leagues":
        # Return the hierarchy
        lines = ["League hierarchy:"]
        lines.append("Continental: " + ", ".join(LEAGUE_HIERARCHY["continental"]))
        lines.append("Top flights: " + ", ".join(LEAGUE_HIERARCHY["top_flights"]))
        lines.append(LEAGUE_HIERARCHY["promotion_relegation_note"])
        send_telegram("\n".join(lines))
    else:
        send_telegram(nigeria_vibe("I no sabi that command. Try: livescores, news, leagues"))

if __name__ == "__main__":
    # When run directly, accept an env var COMMAND for manual testing
    cmd = os.getenv("COMMAND")
    if cmd:
        handle_command(cmd)
    else:
        # Default behavior: post live scores (used by the 15-min workflow)
        post_live_scores()