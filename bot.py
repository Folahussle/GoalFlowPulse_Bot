import requests
import os

# Load secrets from GitHub
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = "@GoalFlowPulse"  # Change to your channel username

def get_scores_and_post():
    url = "https://api.football-data.org/v4/matches"
    headers = {'X-Auth-Token': FOOTBALL_API_KEY}
    
    try:
        response = requests.get(url, headers=headers).json()
        matches = response.get('matches', [])
        
        if not matches:
            print("No matches found right now.")
            return

        for match in matches:
            if match['status'] in ['IN_PLAY', 'FINISHED']:
                home = match['homeTeam']['name']
                away = match['awayTeam']['name']
                h_score = match['score']['fullTime']['home']
                a_score = match['score']['fullTime']['away']
                
                status = "⚽ LIVE UPDATE" if match['status'] == 'IN_PLAY' else "✅ FINAL SCORE"
                message = f"{status}\n\n{home} {h_score} - {a_score} {away}\n\nPowered by GoalPulse ⚡"
                
                # Send to Telegram
                t_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                requests.post(t_url, data={'chat_id': CHANNEL_ID, 'text': message})
                
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    get_scores_and_post()
