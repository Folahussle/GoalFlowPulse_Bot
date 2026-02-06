# utils.py
import datetime

LEAGUE_HIERARCHY = {
    "continental": ["UEFA Champions League", "UEFA Europa League", "UEFA Europa Conference League"],
    "top_flights": ["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1", "MLS", "Saudi Pro League"],
    "promotion_relegation_note": "Most domestic leagues use promotion/relegation; bottom teams drop to lower divisions (e.g., EPL -> Championship)."
}

PRIORITY_CODES = {"CL", "EL", "EC", "PL", "PD", "SA", "BL1", "FL1", "MLS", "SPL"}
PRIORITY_NAMES = set(LEAGUE_HIERARCHY["continental"] + LEAGUE_HIERARCHY["top_flights"])

def nigeria_vibe(text: str) -> str:
    return f"Omo! {text}"

def format_ht_message(comp_name: str, home: str, away: str, home_score, away_score) -> str:
    home_score = home_score if home_score is not None else "-"
    away_score = away_score if away_score is not None else "-"
    return f"{comp_name}\nHT: {home} {home_score}-{away_score} {away}\nOmo! Halftime don land o!"

def format_ft_message(comp_name: str, home: str, away: str, home_score, away_score) -> str:
    home_score = home_score if home_score is not None else "-"
    away_score = away_score if away_score is not None else "-"
    return f"{comp_name}\nFT: {home} {home_score}-{away_score} {away}\nOmo! Match don finish!"