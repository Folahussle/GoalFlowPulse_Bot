# utils.py
import datetime

# League hierarchy and priority lists
LEAGUE_HIERARCHY = {
    "continental": ["UEFA Champions League", "UEFA Europa League", "UEFA Europa Conference League"],
    "top_flights": ["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1", "MLS", "Saudi Pro League"],
    "promotion_relegation_note": "Most domestic leagues use promotion/relegation; bottom teams drop to lower divisions (e.g., EPL -> Championship)."
}

# Priority competition codes (Football-Data.org uses codes like CL, EL, etc.)
PRIORITY_CODES = {"CL", "EL", "EC", "PL", "PD", "SA", "BL1", "FL1", "MLS", "SPL"}  # add codes as you discover them
PRIORITY_NAMES = set(LEAGUE_HIERARCHY["continental"] + LEAGUE_HIERARCHY["top_flights"])

def nigeria_vibe(text: str) -> str:
    """Add a short Nigerian/Lagos style prefix to messages."""
    prefix = "Omo! "
    return f"{prefix}{text}"

def format_score_message(match: dict, channel_name: str) -> str:
    """Format a match dict into a friendly score message with Nigerian vibe."""
    status = match.get("status", "")
    home = match.get("homeTeam", {}).get("name", "Home")
    away = match.get("awayTeam", {}).get("name", "Away")
    # Try fullTime then live
    full = match.get("score", {}).get("fullTime", {}) or {}
    home_score = full.get("home")
    away_score = full.get("away")
    if home_score is None or away_score is None:
        # fallback to live or half-time fields
        live = match.get("score", {}).get("live", {}) or {}
        home_score = home_score if home_score is not None else live.get("home")
        away_score = away_score if away_score is not None else live.get("away")
    home_score = home_score if home_score is not None else "-"
    away_score = away_score if away_score is not None else "-"
    status_text = "FINAL SCORE" if status == "FINISHED" else "LIVE UPDATE ⚽" if status in ("IN_PLAY", "PAUSED") else status
    text = f"{status_text}\n\n{home} {home_score} - {away_score} {away}\n\nStay tuned to {channel_name}"
    return nigeria_vibe(text)

def now_utc_iso() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"