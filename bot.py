# bot.py
import os
import requests
import time
from utils import format_score_message, nigeria_vibe, PRIORITY_CODES, PRIORITY_NAMES
from news_fetcher import get_top_news_unique, mark_news_as_posted

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # e.g., @GoalFlowPulse
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")  # optional

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def send_telegram(text: str, parse_mode: str = None) -> bool:
    data = {"chat_id": CHANNEL_ID, "text": text}
    if parse_mode:
        data["parse_mode"] = parse_mode
    try:
        r = requests.post(f"{TELEGRAM_API}/sendMessage", data=data, timeout=10)
        return r.ok
    except Exception as e:
        print("Telegram send error:", e)
        return False

def post_live_scores(max_posts=10):
    url = "https://api.football-data.org/v4/matches"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        matches = data.get("matches", [])

        # Helper: determine priority score (lower = higher priority)
        def priority_score(match):
            comp = match.get("competition", {})
            code = (comp.get("code") or "").upper()
            name = comp.get("name", "")
            if code in PRIORITY_CODES:
                if code == "CL":
                    return 0
                if code == "EL":
                    return 1
                if code == "EC":
                    return 2
                return 3
            if name in PRIORITY_NAMES:
                return 3
            return 10

        live_statuses = {"IN_PLAY", "PAUSED"}
        finished_statuses = {"FINISHED"}
        relevant = [m for m in matches if m.get("status") in (live_statuses | finished_statuses)]

        def sort_key(m):
            status = m.get("status", "")
            status_rank = 3
            if status == "IN_PLAY":
                status_rank = 0
            elif status == "PAUSED":
                status_rank = 1
            elif status == "FINISHED":
                status_rank = 2
            utc_kickoff = m.get("utcDate") or ""
            return (priority_score(m), status_rank, utc_kickoff)

        relevant_sorted = sorted(relevant, key=sort_key)

        posted = 0
        for m in relevant_sorted:
            if posted >= max_posts:
                break
            comp = m.get("competition", {}).get("name", "Unknown Competition")
            text = format_score_message(m, CHANNEL_ID)
            text = f"{comp}\n\n{text}"
            send_telegram(text)
            posted += 1
            time.sleep(1)

        if posted == 0:
            send_telegram(nigeria_vibe("No live matches right now among the priority competitions."))
    except Exception as e:
        print("Error fetching live scores:", e)
        send_telegram(nigeria_vibe("Error fetching live scores. I go check and come back."))

def post_daily_news():
    headlines = get_top_news_unique(NEWSAPI_KEY, max_items=6)
    if not headlines:
        send_telegram(nigeria_vibe("No new news right now. I no go repost old one."))
        return
    text_lines = ["🔥 Top Football News & Transfer Rumours 🔥\n"]
    for h in headlines:
        title = h.get("title")
        link = h.get("link")
        source = h.get("source", h.get("source", "news"))
        text_lines.append(f"• {title} — {source}\n{link}\n")
    text_lines.append(f"\nFollow {CHANNEL_ID} for live scores and more.")
    ok = send_telegram("\n".join(text_lines))
    if ok:
        mark_news_as_posted(headlines)

def handle_command(command: str):
    cmd = (command or "").strip().lower()
    if cmd == "livescores":
        post_live_scores()
    elif cmd == "news":
        post_daily_news()
    elif cmd == "leagues":
        lines = ["League hierarchy:"]
        lines.append("Continental: " + ", ".join(["UEFA Champions League", "UEFA Europa League", "UEFA Europa Conference League"]))
        lines.append("Top flights: " + ", ".join(["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1", "MLS", "Saudi Pro League"]))
        lines.append("Most domestic leagues use promotion/relegation; bottom teams drop to lower divisions.")
        send_telegram("\n".join(lines))
    else:
        send_telegram(nigeria_vibe("I no sabi that command. Try: livescores, news, leagues"))

if __name__ == "__main__":
    cmd = os.getenv("COMMAND")
    if cmd:
        handle_command(cmd)
    else:
        # Default: post live scores (used by 15-min scheduler)
        post_live_scores()