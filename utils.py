# utils.py
import datetime

# League hierarchy used when user asks about "leagues"
LEAGUE_HIERARCHY = {
    "continental": ["UEFA Champions League", "UEFA Europa League", "UEFA Conference League"],
    "top_flights": ["English Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1", "MLS", "Saudi Pro League"],
    "promotion_relegation_note": "Most domestic leagues use promotion/relegation; bottom teams drop to lower divisions (e.g., EPL -> Championship)."
}

def nigeria_vibe(text):
    # Add a short Nigerian flavor to messages
    prefix = "Omo! "  # short, friendly Lagos vibe
    return f"{prefix}{text}"

def format_score_message(match, channel_name):
    status = match.get("status", "")
    home = match.get("homeTeam", {}).get("name", "Home")
    away = match.get("awayTeam", {}).get("name", "Away")
    # Score fields may be None; handle gracefully
    full = match.get("score", {}).get("fullTime", {})
    home_score = full.get("home")
    away_score = full.get("away")
    if home_score is None or away_score is None:
        # Try live score structure
        live = match.get("score", {}).get("live", {})
        home_score = home_score if home_score is not None else live.get("home")
        away_score = away_score if away_score is not None else live.get("away")
    home_score = home_score if home_score is not None else "-"
    away_score = away_score if away_score is not None else "-"
    status_text = "FINAL SCORE" if status == "FINISHED" else "LIVE UPDATE ⚽" if status == "IN_PLAY" else status
    text = f"{status_text}\n\n{home} {home_score} - {away_score} {away}\n\nStay tuned to {channel_name}"
    return nigeria_vibe(text)

def now_utc_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"