import os
import asyncio
import logging
import feedparser  # For reading news feeds
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
# ⚠️ SECURITY: Keys are loaded from environment variables (Secrets)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
CHANNEL_NAME = os.getenv("CHANNEL_NAME")

# Setup Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- 1. EXPERT KNOWLEDGE BASE ---
# Hierarchy: Continental > Big 5 > Others
LEAGUES = {
    # Continental (Tier 1)
    'CL': {'id': 2001, 'name': 'Champions League', 'tier': 1, 'emoji': '🏆'},
    'EC': {'id': 2018, 'name': 'Euro Championship', 'tier': 1, 'emoji': '🇪🇺'},
    
    # Domestic Big 5 (Tier 2)
    'PL': {'id': 2021, 'name': 'Premier League', 'tier': 2, 'emoji': '🏴󠁧󠁢󠁥󠁮󠁧󠁿'},
    'PD': {'id': 2014, 'name': 'La Liga', 'tier': 2, 'emoji': '🇪🇸'},
    'SA': {'id': 2019, 'name': 'Serie A', 'tier': 2, 'emoji': '🇮🇹'},
    'BL1': {'id': 2002, 'name': 'Bundesliga', 'tier': 2, 'emoji': '🇩🇪'},
    'FL1': {'id': 2015, 'name': 'Ligue 1', 'tier': 2, 'emoji': '🇫🇷'},
    
    # Global & Others (Tier 3)
    'ELC': {'id': 2016, 'name': 'Championship', 'tier': 3, 'emoji': '🦁'}, # Promotion/Relegation awareness
    'DED': {'id': 2003, 'name': 'Eredivisie', 'tier': 3, 'emoji': '🇳🇱'},
    'BSA': {'id': 2013, 'name': 'Brasileirão', 'tier': 3, 'emoji': '🇧🇷'},
}

# Reliable News Sources for Cross-Referencing
RSS_FEEDS = [
    "http://feeds.bbci.co.uk/sport/football/rss.xml",       # BBC (High Reliability)
    "https://www.skysports.com/rss/12040",                 # Sky Sports
    "https://www.theguardian.com/football/rss",            # Guardian
    "https://talksport.com/feed/",                         # TalkSport (Good for rumors)
]

# The "Nigerian Vibe" Dictionary
VIBES = [
    "Abeg, gather here!", 
    "Omo, see updates!", 
    "No dulling, see wetin dey sup!", 
    "Football don land!", 
    "Una good morning o! See fresh gist.",
    "E don set! Check these scores.",
    "Na wa o! See wetin dey happen."
]

# --- 2. CORE FUNCTIONS ---

def get_vibe():
    """Returns a random Nigerian phrase."""
    import random
    return random.choice(VIBES)

async def fetch_verified_news():
    """
    Fetches news from multiple sources and cross-references them.
    If a story appears in >1 source, it's considered 'Verified'.
    """
    articles = []
    
    # 1. Fetch all stories
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]: # Check top 10 from each
                articles.append(entry.title)
        except Exception as e:
            logging.error(f"Feed error: {e}")

    # 2. Cross-Reference Logic (Finding "Prominently Occurring" stories)
    # We compare titles to find similar stories across sources
    verified_stories = []
    seen_indices = set()

    for i in range(len(articles)):
        if i in seen_indices: continue
        
        duplicates = 0
        current_title = articles[i]
        
        for j in range(i + 1, len(articles)):
            if j in seen_indices: continue
            
            # Similarity check (0.6 means 60% similar)
            ratio = SequenceMatcher(None, current_title, articles[j]).ratio()
            if ratio > 0.5: 
                duplicates += 1
                seen_indices.add(j)
        
        # If duplicated at least once, it's a hot topic/verified
        if duplicates > 0:
            verified_stories.append(current_title)
            seen_indices.add(i)

    return verified_stories[:5] # Return top 5 hottest stories

async def fetch_matches(status="SCHEDULED"):
    """Fetches matches from Football-Data.org"""
    matches = []
    headers = {'X-Auth-Token': FOOTBALL_API_KEY}
    
    # Date range: Today
    today = datetime.now().strftime('%Y-%m-%d')
    
    async with httpx.AsyncClient() as client:
        # We iterate through our Expert Hierarchy
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
                        'time': m['utcDate'], # ISO format
                        'id': m['id']
                    } for m in data['matches']])
                
                await asyncio.sleep(1) # Respect API limits (10 req/min)
            except Exception as e:
                logging.error(f"API Error ({code}): {e}")
                
    # Sort by Tier (Champions League first, then Big 5)
    matches.sort(key=lambda x: x['tier'])
    return matches

# --- 3. TELEGRAM ACTIONS ---

async def post_daily_news(context: ContextTypes.DEFAULT_TYPE):
    """Automated Job: Posts News at 8:30 AM/PM"""
    hot_stories = await fetch_verified_news()
    
    if not hot_stories:
        return # Quiet if no major news

    msg = f"🗞️ *GOALFLOW PULSE UPDATE* 🗞️\n\n{get_vibe()}\n\n"
    msg += "*🔥 VERIFIED TRENDING GIST:*\n"
    
    for i, story in enumerate(hot_stories, 1):
        msg += f"{i}. {story}\n"
    
    msg += "\n_Source: Cross-referenced from BBC, Sky & Guardian_"
    
    await context.bot.send_message(chat_id=CHANNEL_NAME, text=msg, parse_mode=ParseMode.MARKDOWN)

async def post_live_scores(context: ContextTypes.DEFAULT_TYPE):
    """Posts scorelines for completed/live matches"""
    matches = await fetch_matches(status="FINISHED,IN_PLAY")
    
    if not matches: return

    msg = f"⚽ *LATEST SCOREBOARD* ⚽\n\n"
    current_league = ""
    
    for m in matches:
        # League Header
        if m['league'] != current_league:
            msg += f"\n{m['emoji']} *{m['league']}*\n"
            current_league = m['league']
            
        score_str = f"{m['score']['home']} - {m['score']['away']}"
        # Handle None scores for matches just starting
        if m['score']['home'] is None: score_str = "0 - 0"
        
        msg += f"• {m['home']}  {score_str}  {m['away']}\n"

    await context.bot.send_message(chat_id=CHANNEL_NAME, text=msg, parse_mode=ParseMode.MARKDOWN)

async def manage_polls(context: ContextTypes.DEFAULT_TYPE):
    """Creates polls for upcoming 'Top Tier' matches"""
    # Fetch scheduled matches
    matches = await fetch_matches(status="SCHEDULED")
    
    # Filter for 'Big Matches' (Tier 1 & 2 only)
    big_matches = [m for m in matches if m['tier'] <= 2]

    for match in big_matches:
        # Calculate start time
        match_time = datetime.fromisoformat(match['time'].replace('Z', '+00:00'))
        now = datetime.now(match_time.tzinfo)
        
        # Only post poll if match is between 3 to 6 hours away
        hours_until = (match_time - now).total_seconds() / 3600
        if 3 <= hours_until <= 6:
            question = f"{match['emoji']} {match['league']}: Who wins?\n{match['home']} vs {match['away']}"
            options = [f"✅ {match['home']}", "🤝 Draw", f"✅ {match['away']}"]
            
            # Send Poll
            poll_msg = await context.bot.send_poll(
                chat_id=CHANNEL_NAME,
                question=question,
                options=options,
                is_anonymous=True
            )
            
            # Schedule Poll Closing (10 mins before Kickoff)
            close_time = match_time - timedelta(minutes=10)
            context.job_queue.run_once(
                close_poll_job,
                when=close_time,
                data={'poll_id': poll_msg.poll.id, 'match': f"{match['home']} vs {match['away']}"},
                name=str(match['id'])
            )

async def close_poll_job(context: ContextTypes.DEFAULT_TYPE):
    """Stops the poll and announces voting closed"""
    job_data = context.job.data
    poll_id = job_data['poll_id']
    match_name = job_data['match']
    
    try:
        await context.bot.stop_poll(chat_id=CHANNEL_NAME, message_id=poll_id)
        await context.bot.send_message(
            chat_id=CHANNEL_NAME,
            text=f"🗳️ *VOTING CLOSED* for {match_name}!\n\nMatch kicks off in 10 mins! Oya let's go! 🚀"
        )
    except Exception as e:
        logging.error(f"Failed to close poll: {e}")

# --- 4. MAIN EXECUTION ---

if __name__ == '__main__':
    # Initialize Bot
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Setup Scheduler
    scheduler = AsyncIOScheduler()
    
    # News: 8:30 AM & 8:30 PM
    scheduler.add_job(post_daily_news, CronTrigger(hour=8, minute=30))
    scheduler.add_job(post_daily_news, CronTrigger(hour=20, minute=30))
    
    # Scores: Every 2 hours
    scheduler.add_job(post_live_scores, CronTrigger(minute=0, hour='12-23/2'))
    
    # Polls: Check for new matches every 4 hours
    scheduler.add_job(manage_polls, CronTrigger(minute=15, hour='*/4'))
    
    # Add scheduler to bot
    application.job_queue.scheduler = scheduler
    scheduler.start()

    print("GoalFlowPulse Bot is LIVE! 🚀")
    application.run_polling()
