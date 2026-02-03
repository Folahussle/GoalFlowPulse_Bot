import requests
import os
from datetime import datetime

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
CHANNEL_ID = "@GoalFlowPulse"  # Replace with your channel username

# List of major leagues to filter
MAJOR_LEAGUES = [
    "Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1",
    "Liga Portugal", "Eredivisie", "Belgian Pro League", "Scottish Premiership", "Süper Lig",
    "MLS", "Liga MX", "Campeonato Brasileiro Série A", "Argentine Primera División",
    "Saudi Pro League", "J1 League", "A-League"
]

def get_scores_and_post():
    url = "https://api.football-data.org/v4/matches"
    headers = {'X-Auth-Token': FOOTBALL_API_KEY}
    try:
        response = requests.get(url, headers=headers).json()
        for match in response.get('matches', []):
            if match['status'] in ['IN_PLAY', 'FINISHED']:
                home = match['homeTeam']['name']
                away = match['awayTeam']['name']
                h_score = match['score']['fullTime']['home']
                a_score = match['score']['fullTime']['away']
                status = "⚽ LIVE UPDATE" if match['status'] == 'IN_PLAY' else "✅ FINAL SCORE"
                message = f"{status}\n\n{home} {h_score} - {a_score} {away}\n\nPowered by GoalPulse ⚡"
                send_to_telegram(message)
    except Exception as e:
        print(f"Error occurred: {e}")

def get_news_and_post():
    url = f"https://newsapi.org/v2/top-headlines?category=sports&q=football&language=en&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(url).json()
        articles = response.get('articles', [])
        if not articles:
            print("No news found.")
            return

        # Filter articles by major leagues
        filtered_articles = [
            article for article in articles
            if any(league.lower() in article['title'].lower() for league in MAJOR_LEAGUES)
        ]

        # Post top 3 filtered headlines
        for article in filtered_articles[:3]:
            title = article['title']
            source = article['source']['name']
            message = f"📰 {title}\n(Source: {source})\n\nStay tuned @GoalPulseUpdates"
            send_to_telegram(message)

    except Exception as e:
        print(f"Error fetching news: {e}")

def send_to_telegram(message):
    t_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(t_url, data={'chat_id': CHANNEL_ID, 'text': message})

if __name__ == "__main__":
    hour = datetime.now().hour
    if hour == 9:   # Morning
        get_news_and_post()
    elif hour == 21:  # Night
        get_news_and_post()
    else:
        get_scores_and_post()
