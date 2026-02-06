import os
import asyncio
import logging
import feedparser
import httpx
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from telegram import Update, Poll
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
CHANNEL_NAME = os.getenv("CHANNEL_NAME")

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- MEMORY (To prevent duplicate alerts) ---
processed_alerts = set() # Stores IDs of matches/events we've already posted about

# --- 1. EXPERT KNOWLEDGE BASE ---
LEAGUES = {
    'CL': {'id': 2001, 'name': 'Champions League', 'tier': 1, 'emoji': '🏆'},
    'PL': {'id': 2021, 'name': 'Premier League', 'tier': 2, 'emoji': '🏴󠁧󠁢󠁥󠁮󠁧󠁿'},
    'PD': {'id': 2014, 'name': 'La Liga', 'tier': 2, 'emoji': '🇪🇸'},
    'SA': {'id': 2019, 'name': 'Serie A', 'tier': 2, 'emoji': '🇮🇹'},
    'BL1': {'id': 2002, 'name': 'Bundesliga', 'tier': 2, 'emoji': '🇩🇪'},
    'FL1': {'id': 2015, 'name': 'Ligue 1', 'tier': 2, 'emoji': '🇫🇷'},
}

# "Giants" List for Upset Detection
GIANTS = [
    "Man City", "Liverpool", "Arsenal", "Real Madrid", "Barcelona", 
    "Bayern", "PSG", "Inter", "Juventus", "Milan"
]

RSS_FEEDS = [
    "http://feeds.bbci.co.uk/sport/football/rss.xml",
    "https://www.skysports.com/rss/12040",
    "https://www.theguardian.com/football/rss",
    "https://talksport.com/feed/"
]

VIBES = [
    "Abeg, gather here!", "Omo, see updates!", "No dulling!", 
    "Football don land!", "Na wa o! See wetin dey happen."
]

# --- 2. CORE FUNCTIONS ---

def get_vibe():
    import random
    return random.choice(VIBES)

async def fetch_verified_news():
    """Fetches news + Checks for Transfer Market keywords"""
    articles = []
    transfer_keywords = ["here we go", "deal done", "medical", "agreed", "breaking"]
    
    # 1. Fetch
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                title = entry.title
                # Priority Check: Transfers
                is_transfer = any(k in title.lower() for k in transfer_keywords)
                if is_transfer:
                    title = f"🚨 TRANSFER ALERT: {title}" 
                articles.append(title)
        except Exception as e:
            logging.error(f"Feed error: {e}")

    # 2. Cross-Reference (Simple verify)
    verified_stories = []
    seen_indices = set()
    for i in range(len(articles)):
        if i in seen_indices: continue
        duplicates = 0
        for j in range(i + 1, len(articles)):
            if j in seen_indices: continue
            if SequenceMatcher(None, articles[i], articles[j]).ratio() > 0.5: 
                duplicates += 1
                seen_indices.add(j)
        
        # If duplicated OR it's a transfer alert, keep it
        if duplicates > 0 or "TRANSFER ALERT" in articles[i]:
            verified_stories.append(articles[i])
            seen_indices.add(i)

    return verified_stories[:5]

async def fetch_matches(status="SCHEDULED"):
    matches = []
    headers = {'X-Auth-Token': FOOTBALL_API_KEY}
    today = datetime.now().strftime('%Y-%m-%d')
    
    async with httpx.AsyncClient() as client:
        for code, info in LEAGUES.items():
            try:
                url = f"https://api.football-data.org/v4/competitions/{code}/matches"
                params = {'dateFrom': today, 'dateTo': today, 'status': status}
                resp = await client.get(url, headers=headers, params=params)
                data = resp.json()
                if 'matches' in data:
                    matches.extend([{
                        'league': info['name'],
                        'tier': info['tier'],
                        'emoji': info['emoji'],
                        'home': m['homeTeam']['name'],
                        'away': m['awayTeam']['name'],
                        'score': m['score']['fullTime'],
                        'half_score': m['score']['halfTime'],
                        'status': m['status'],
                        'time': m['utcDate'],
                        'id': m['id']
                    } for m in data['matches']])
                await asyncio.sleep(1) 
            except Exception: continue
    return matches

# --- 3. TELEGRAM ACTIONS ---

async def post_daily_news(context: ContextTypes.DEFAULT_TYPE):
    hot_stories = await fetch_verified_news()
    if not hot_stories: return

    msg = f"🗞️ *GOALFLOW PULSE UPDATE* 🗞️\n\n{get_vibe()}\n\n"
    for i, story in enumerate(hot_stories, 1):
        msg += f"{i}. {story}\n"
    
    await context.bot.send_message(chat_id=CHANNEL_NAME, text=msg, parse_mode=ParseMode.MARKDOWN)

async def post_live_scores_and_alerts(context: ContextTypes.DEFAULT_TYPE):
    """Handles Scores, Halftime Polls, and Upset Alerts"""
    matches = await fetch_matches(status="FINISHED,IN_PLAY,PAUSED")
    if not matches: return

    msg = f"⚽ *LATEST SCOREBOARD* ⚽\n\n"
    
    for m in matches:
        home_score = m['score']['home'] if m['score']['home'] is not None else 0
        away_score = m['score']['away'] if m['score']['away'] is not None else 0
        
        # 1. UPSET ALERT (Big Team Losing)
        alert_id = f"upset_{m['id']}"
        if alert_id not in processed_alerts:
            losing_giant = None
            if m['home'] in GIANTS and home_score < away_score: losing_giant = m['home']
            if m['away'] in GIANTS and away_score < home_score: losing_giant = m['away']
            
            if losing_giant:
                upset_msg = f"🚨 *UPSET ALERT!* 🚨\n\n{losing_giant} is LOSING!\n{m['home']} {home_score} - {away_score} {m['away']}"
                await context.bot.send_message(chat_id=CHANNEL_NAME, text=upset_msg, parse_mode=ParseMode.MARKDOWN)
                processed_alerts.add(alert_id)

        # 2. HALFTIME POLL
        ht_id = f"ht_{m['id']}"
        if m['status'] == 'PAUSED' and ht_id not in processed_alerts:
            poll_q = f"HT: {m['home']} {home_score}-{away_score} {m['away']}\nWho wins Full Time?"
            await context.bot.send_poll(chat_id=CHANNEL_NAME, question=poll_q, options=[m['home'], "Draw", m['away']])
            processed_alerts.add(ht_id)

        msg += f"{m['emoji']} {m['home']} {home_score} - {away_score} {m['away']}\n"

    # Only post scoreboard if it's a scheduled update (checking context)
    # This function runs often for alerts, but we can limit full board posting
    if context.job and context.job.name == 'scoreboard':
        await context.bot.send_message(chat_id=CHANNEL_NAME, text=msg, parse_mode=ParseMode.MARKDOWN)

async def manage_polls(context: ContextTypes.DEFAULT_TYPE):
    matches = await fetch_matches(status="SCHEDULED")
    big_matches = [m for m in matches if m['tier'] <= 2]

    for match in big_matches:
        match_time = datetime.fromisoformat(match['time'].replace('Z', '+00:00'))
        hours_until = (match_time - datetime.now(match_time.tzinfo)).total_seconds() / 3600
        
        # Poll 3-6 hours before
        if 3 <= hours_until <= 6:
            q = f"{match['emoji']} {match['league']}: Who wins?\n{match['home']} vs {match['away']}"
            msg = await context.bot.send_poll(chat_id=CHANNEL_NAME, question=q, options=[match['home'], "Draw", match['away']])
            
            # Close 10 mins before
            close_time = match_time - timedelta(minutes=10)
            context.job_queue.run_once(close_poll_job, when=close_time, data={'poll_id': msg.poll.id, 'match': f"{match['home']} vs {match['away']}"})

async def close_poll_job(context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.stop_poll(chat_id=CHANNEL_NAME, message_id=context.job.data['poll_id'])
        await context.bot.send_message(chat_id=CHANNEL_NAME, text=f"🗳️ Voting Closed for {context.job.data['match']}! Kickoff soon!")
    except: pass

# --- 4. MAIN ---
if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    scheduler = AsyncIOScheduler()
    
    # News (8:30 AM & PM)
    scheduler.add_job(post_daily_news, CronTrigger(hour=8, minute=30))
    scheduler.add_job(post_daily_news, CronTrigger(hour=20, minute=30))
    
    # Live Checks (Scores/Alerts) every 10 mins
    scheduler.add_job(post_live_scores_and_alerts, CronTrigger(minute='*/10'))
    
    # Full Scoreboard post every 2 hours
    scheduler.add_job(post_live_scores_and_alerts, CronTrigger(minute=0, hour='12-23/2'), name='scoreboard')
    
    # Pre-match Polls
    scheduler.add_job(manage_polls, CronTrigger(minute=15, hour='*/4'))
    
    application.job_queue.scheduler = scheduler
    scheduler.start()
    print("GoalFlowPulse 2.0 (Smart Alert Edition) is LIVE! 🚀")
    application.run_polling()
