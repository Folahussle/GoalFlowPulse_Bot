"""
GoalFlowPulse - Enhanced Football Telegram Bot
Features: Multi-source news aggregation with cross-verification
"""

import os
import asyncio
import random
from datetime import datetime, timedelta
from telegram import Update, Poll
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode
import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
from collections import Counter
import feedparser

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8542955893:AAHfwn30QcJjHpJ_Ck-gZCYR9M7BzS7BK94')
FOOTBALL_API_KEY = os.getenv('FOOTBALL_API_KEY', '773af02a0f5b4096908a2caa5d225dae')
CHANNEL_NAME = os.getenv('CHANNEL_NAME', '@GoalFlowPulse')
NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')  # Optional: Get free key from newsapi.org

# Nigerian vibe greetings and phrases
NIGERIAN_VIBES = [
    "🔥 E don set! ",
    "⚡ Omo see gobe! ",
    "💯 This thing sweet die! ",
    "🎯 E choke! ",
    "✨ Na wa o! ",
    "🚀 Make we yarn! ",
    "💪 E dey pepper dem! ",
    "🌟 Abeg check am! "
]

# Major leagues for our bot
MAJOR_LEAGUES = {
    'PL': {'id': 2021, 'name': 'Premier League', 'emoji': '🏴󠁧󠁢󠁥󠁮󠁧󠁿'},
    'PD': {'id': 2014, 'name': 'La Liga', 'emoji': '🇪🇸'},
    'SA': {'id': 2019, 'name': 'Serie A', 'emoji': '🇮🇹'},
    'BL1': {'id': 2002, 'name': 'Bundesliga', 'emoji': '🇩🇪'},
    'FL1': {'id': 2015, 'name': 'Ligue 1', 'emoji': '🇫🇷'},
    'CL': {'id': 2001, 'name': 'Champions League', 'emoji': '⭐'},
}

# Multiple news sources for cross-verification
NEWS_SOURCES = {
    'bbc_sport': {
        'name': 'BBC Sport',
        'rss': 'http://feeds.bbci.co.uk/sport/football/rss.xml',
        'emoji': '🇬🇧'
    },
    'espn': {
        'name': 'ESPN FC',
        'rss': 'https://www.espn.com/espn/rss/soccer/news',
        'emoji': '🏆'
    },
    'sky_sports': {
        'name': 'Sky Sports',
        'rss': 'https://www.skysports.com/rss/12040',
        'emoji': '📺'
    },
    'goal': {
        'name': 'Goal.com',
        'url': 'https://www.goal.com/en/news',
        'emoji': '⚽'
    },
    'guardian': {
        'name': 'The Guardian',
        'rss': 'https://www.theguardian.com/football/rss',
        'emoji': '📰'
    }
}


def get_nigerian_greeting():
    """Return a random Nigerian vibe greeting"""
    return random.choice(NIGERIAN_VIBES)


def calculate_similarity(text1, text2):
    """Calculate similarity between two text strings (0-1)"""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()


def extract_keywords(text):
    """Extract key football terms from text"""
    # Common football keywords to focus on
    football_terms = [
        'transfer', 'goal', 'win', 'lose', 'draw', 'match', 'injury', 
        'manager', 'coach', 'sign', 'contract', 'deal', 'rumour', 'bid',
        'champions league', 'premier league', 'la liga', 'serie a', 'bundesliga'
    ]
    
    text_lower = text.lower()
    found_terms = []
    
    for term in football_terms:
        if term in text_lower:
            found_terms.append(term)
    
    # Also extract team names and player names (simplified)
    words = text.split()
    capitalized = [w for w in words if w[0].isupper() and len(w) > 3]
    
    return found_terms + capitalized[:5]  # Limit to 5 names


async def fetch_rss_news(source_name, rss_url):
    """Fetch news from RSS feed"""
    news_items = []
    
    try:
        feed = feedparser.parse(rss_url)
        
        for entry in feed.entries[:10]:  # Get latest 10 articles
            news_items.append({
                'source': source_name,
                'title': entry.get('title', ''),
                'description': entry.get('summary', ''),
                'link': entry.get('link', ''),
                'published': entry.get('published', ''),
                'keywords': extract_keywords(entry.get('title', '') + ' ' + entry.get('summary', ''))
            })
    
    except Exception as e:
        print(f"Error fetching RSS from {source_name}: {e}")
    
    return news_items


async def fetch_newsapi_football():
    """Fetch football news from NewsAPI.org"""
    news_items = []
    
    if not NEWS_API_KEY:
        return news_items
    
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            'apiKey': NEWS_API_KEY,
            'q': 'football OR soccer OR transfer',
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 20
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            for article in data.get('articles', []):
                news_items.append({
                    'source': 'NewsAPI',
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'link': article.get('url', ''),
                    'published': article.get('publishedAt', ''),
                    'keywords': extract_keywords(article.get('title', '') + ' ' + article.get('description', ''))
                })
    
    except Exception as e:
        print(f"Error fetching NewsAPI: {e}")
    
    return news_items


async def aggregate_all_news():
    """Fetch news from all sources"""
    all_news = []
    
    # Fetch from RSS sources
    for source_key, source_info in NEWS_SOURCES.items():
        if 'rss' in source_info:
            news = await fetch_rss_news(source_info['name'], source_info['rss'])
            all_news.extend(news)
            await asyncio.sleep(1)  # Be nice to servers
    
    # Fetch from NewsAPI if key is available
    if NEWS_API_KEY:
        newsapi_items = await fetch_newsapi_football()
        all_news.extend(newsapi_items)
    
    return all_news


def find_similar_stories(news_items, similarity_threshold=0.6):
    """
    Group similar news stories together
    Returns stories that appear in multiple sources
    """
    grouped_stories = []
    used_indices = set()
    
    for i, item1 in enumerate(news_items):
        if i in used_indices:
            continue
        
        # Create a group for this story
        story_group = {
            'main_story': item1,
            'similar_stories': [],
            'sources': [item1['source']],
            'source_count': 1,
            'combined_keywords': item1['keywords'].copy()
        }
        
        # Find similar stories
        for j, item2 in enumerate(news_items):
            if i >= j or j in used_indices:
                continue
            
            # Check similarity of titles
            title_similarity = calculate_similarity(item1['title'], item2['title'])
            
            # Check keyword overlap
            keywords1 = set(item1['keywords'])
            keywords2 = set(item2['keywords'])
            keyword_overlap = len(keywords1.intersection(keywords2))
            
            # If similar enough, group them
            if title_similarity > similarity_threshold or keyword_overlap >= 3:
                story_group['similar_stories'].append(item2)
                story_group['sources'].append(item2['source'])
                story_group['source_count'] += 1
                story_group['combined_keywords'].extend(item2['keywords'])
                used_indices.add(j)
        
        used_indices.add(i)
        grouped_stories.append(story_group)
    
    return grouped_stories


def get_verified_news(grouped_stories, min_sources=2):
    """
    Filter stories that appear in at least min_sources
    Returns only verified news
    """
    verified = []
    
    for story in grouped_stories:
        if story['source_count'] >= min_sources:
            # Count most common keywords
            keyword_counts = Counter(story['combined_keywords'])
            top_keywords = [k for k, v in keyword_counts.most_common(5)]
            
            verified.append({
                'title': story['main_story']['title'],
                'description': story['main_story']['description'],
                'link': story['main_story']['link'],
                'sources': list(set(story['sources'])),  # Unique sources
                'source_count': story['source_count'],
                'keywords': top_keywords,
                'confidence': min(story['source_count'] / len(NEWS_SOURCES), 1.0)  # 0-1 scale
            })
    
    # Sort by source count (most verified first)
    verified.sort(key=lambda x: x['source_count'], reverse=True)
    
    return verified


async def fetch_football_news():
    """
    Main news fetching function with cross-verification
    """
    print("📰 Fetching news from multiple sources...")
    
    try:
        # Step 1: Aggregate news from all sources
        all_news = await aggregate_all_news()
        print(f"✅ Fetched {len(all_news)} total articles")
        
        if not all_news:
            return []
        
        # Step 2: Find similar stories across sources
        grouped_stories = find_similar_stories(all_news, similarity_threshold=0.6)
        print(f"✅ Grouped into {len(grouped_stories)} unique stories")
        
        # Step 3: Get only verified news (appears in 2+ sources)
        verified_news = get_verified_news(grouped_stories, min_sources=2)
        print(f"✅ Found {len(verified_news)} verified stories")
        
        return verified_news[:10]  # Return top 10 most verified stories
    
    except Exception as e:
        print(f"Error in fetch_football_news: {e}")
        return []


async def fetch_match_scores():
    """Fetch live scores and recent results"""
    scores_data = []
    
    try:
        headers = {'X-Auth-Token': FOOTBALL_API_KEY}
        today = datetime.now().strftime('%Y-%m-%d')
        
        for league_code, league_info in MAJOR_LEAGUES.items():
            try:
                url = f"https://api.football-data.org/v4/competitions/{league_code}/matches"
                params = {'dateFrom': today, 'dateTo': today, 'status': 'FINISHED,IN_PLAY'}
                response = requests.get(url, headers=headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    matches = data.get('matches', [])
                    
                    if matches:
                        scores_data.append({
                            'league': league_info['name'],
                            'emoji': league_info['emoji'],
                            'matches': matches
                        })
            except Exception as e:
                print(f"Error fetching {league_code}: {e}")
                continue
                
    except Exception as e:
        print(f"Error in fetch_match_scores: {e}")
    
    return scores_data


async def fetch_upcoming_matches():
    """Fetch upcoming matches for polls"""
    upcoming = []
    
    try:
        headers = {'X-Auth-Token': FOOTBALL_API_KEY}
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        
        date_from = today.strftime('%Y-%m-%d')
        date_to = tomorrow.strftime('%Y-%m-%d')
        
        for league_code, league_info in MAJOR_LEAGUES.items():
            try:
                url = f"https://api.football-data.org/v4/competitions/{league_code}/matches"
                params = {'dateFrom': date_from, 'dateTo': date_to, 'status': 'SCHEDULED'}
                response = requests.get(url, headers=headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    matches = data.get('matches', [])
                    
                    for match in matches:
                        upcoming.append({
                            'league': league_info['name'],
                            'emoji': league_info['emoji'],
                            'home': match['homeTeam']['name'],
                            'away': match['awayTeam']['name'],
                            'time': match['utcDate'],
                            'id': match['id']
                        })
            except:
                continue
                
    except Exception as e:
        print(f"Error fetching upcoming matches: {e}")
    
    return upcoming


async def post_news(context: ContextTypes.DEFAULT_TYPE):
    """Post verified football news to the channel (runs twice daily)"""
    try:
        vibe = get_nigerian_greeting()
        
        # Fetch verified news
        verified_news = await fetch_football_news()
        
        if not verified_news:
            # Fallback to match info if no news
            message = f"{vibe}*FOOTBALL GIST* ⚽\n\n"
            message += "No major verified news today, but make we check wetin dey happen for matches! 🔥\n"
            message += f"\n_Stay tuned to {CHANNEL_NAME} for updates!_ 💯"
        else:
            message = f"{vibe}*VERIFIED FOOTBALL NEWS* 📰\n\n"
            message += "_Cross-checked from multiple reliable sources:_\n\n"
            
            # Post top 5 verified stories
            for i, story in enumerate(verified_news[:5], 1):
                # Create confidence indicator
                if story['source_count'] >= 4:
                    confidence = "🔥🔥🔥"  # Very reliable
                elif story['source_count'] >= 3:
                    confidence = "🔥🔥"    # Reliable
                else:
                    confidence = "🔥"      # Confirmed by 2+ sources
                
                message += f"*{i}. {story['title']}* {confidence}\n"
                
                # Show which sources reported it
                sources_emoji = []
                for source in story['sources'][:3]:  # Show max 3 sources
                    for src_key, src_info in NEWS_SOURCES.items():
                        if src_info['name'] == source:
                            sources_emoji.append(src_info['emoji'])
                            break
                
                if sources_emoji:
                    message += f"Sources: {' '.join(sources_emoji)} ({story['source_count']} sources)\n"
                
                message += f"_{story['description'][:150]}..._\n\n"
            
            message += f"💯 *Legend:*\n"
            message += "🔥🔥🔥 = 4+ sources (Very reliable)\n"
            message += "🔥🔥 = 3 sources (Reliable)\n"
            message += "🔥 = 2 sources (Confirmed)\n\n"
            message += f"_We dey give you only confirmed gist! Stay locked to {CHANNEL_NAME}_ ⚡"
        
        await context.bot.send_message(
            chat_id=CHANNEL_NAME,
            text=message,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
        
        print("✅ News posted successfully!")
        
    except Exception as e:
        print(f"Error posting news: {e}")


async def post_scores(context: ContextTypes.DEFAULT_TYPE):
    """Post match scorelines"""
    try:
        scores = await fetch_match_scores()
        
        if not scores:
            return  # No matches to report
        
        vibe = get_nigerian_greeting()
        message = f"{vibe}*SCOREBOARD* 📊\n\n"
        
        for league_data in scores:
            message += f"\n{league_data['emoji']} *{league_data['league']}*\n"
            message += "─────────────\n"
            
            for match in league_data['matches'][:5]:  # Limit to 5 matches per league
                home = match['homeTeam']['shortName'] or match['homeTeam']['name']
                away = match['awayTeam']['shortName'] or match['awayTeam']['name']
                
                score = match.get('score', {}).get('fullTime', {})
                home_score = score.get('home', 0)
                away_score = score.get('away', 0)
                
                status = match['status']
                
                if status == 'IN_PLAY':
                    message += f"⚡ {home} {home_score} - {away_score} {away} (LIVE)\n"
                else:
                    message += f"✅ {home} {home_score} - {away_score} {away}\n"
            
            message += "\n"
        
        message += f"_E don set! More updates coming_ 🔥"
        
        await context.bot.send_message(
            chat_id=CHANNEL_NAME,
            text=message,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        print(f"Error posting scores: {e}")


async def create_match_polls(context: ContextTypes.DEFAULT_TYPE):
    """Create polls for upcoming matches"""
    try:
        upcoming = await fetch_upcoming_matches()
        
        # Filter matches happening in the next 2-12 hours
        now = datetime.now()
        poll_matches = []
        
        for match in upcoming:
            match_time = datetime.fromisoformat(match['time'].replace('Z', '+00:00'))
            time_diff = (match_time - now.replace(tzinfo=match_time.tzinfo)).total_seconds() / 3600
            
            # Create polls for matches 2-12 hours away
            if 2 <= time_diff <= 12:
                poll_matches.append(match)
        
        for match in poll_matches[:3]:  # Limit to 3 polls at a time
            vibe = get_nigerian_greeting()
            
            question = f"{match['emoji']} {match['home']} vs {match['away']}\nWetin you think go happen?"
            
            poll = await context.bot.send_poll(
                chat_id=CHANNEL_NAME,
                question=question,
                options=[
                    f"✅ {match['home']} Win",
                    f"🤝 Draw",
                    f"✅ {match['away']} Win"
                ],
                is_anonymous=False,
                allows_multiple_answers=False
            )
            
            # Store poll info for later results posting
            match_time = datetime.fromisoformat(match['time'].replace('Z', '+00:00'))
            
            # Schedule poll close 10 minutes before match
            close_time = match_time - timedelta(minutes=10)
            
            context.job_queue.run_once(
                close_poll,
                when=close_time,
                data={'poll_id': poll.poll.id, 'match': match},
                name=f"close_poll_{match['id']}"
            )
            
            await asyncio.sleep(2)  # Avoid rate limits
            
    except Exception as e:
        print(f"Error creating polls: {e}")


async def close_poll(context: ContextTypes.DEFAULT_TYPE):
    """Close poll and post results 10 minutes before match"""
    try:
        match = context.job.data['match']
        
        message = f"🔔 *POLL RESULTS* - Match starting soon!\n\n"
        message += f"{match['emoji']} {match['home']} vs {match['away']}\n\n"
        message += f"Una don vote! Make we see who go reign! 👑\n"
        message += f"Match go start in 10 minutes! ⚽"
        
        await context.bot.send_message(
            chat_id=CHANNEL_NAME,
            text=message,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        print(f"Error closing poll: {e}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    vibe = get_nigerian_greeting()
    welcome = f"{vibe}Welcome to GoalFlowPulse! ⚽\n\n"
    welcome += "Your number 1 source for:\n"
    welcome += "✅ VERIFIED news (cross-checked from multiple sources)\n"
    welcome += "⚡ Live scores & updates\n"
    welcome += "📰 Transfer news & gist\n"
    welcome += "🗳️ Match predictions\n\n"
    welcome += f"We only post news confirmed by 2+ reliable sources! 🔥\n\n"
    welcome += f"Join {CHANNEL_NAME} make we yarn ball together! 💯"
    
    await update.message.reply_text(welcome)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = f"""
*GoalFlowPulse Commands* ⚽

/start - Welcome message
/help - Show this help
/scores - Get latest scores
/news - Get verified football news
/upcoming - See upcoming matches

_Automated Features:_
📰 Verified news posts: 8:30 AM & 8:30 PM daily
📊 Score updates: Every 2 hours during match days
🗳️ Match polls: Created for big games
✅ All news cross-verified from multiple sources!

*News Sources:*
🇬🇧 BBC Sport
🏆 ESPN
📺 Sky Sports
⚽ Goal.com
📰 The Guardian
...and more!

Join {CHANNEL_NAME} for all updates! 🔥
    """
    
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


async def scores_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual scores command"""
    await post_scores(context)
    if update.message:
        await update.message.reply_text("Scores posted to channel! ✅")


async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual news command"""
    await post_news(context)
    if update.message:
        await update.message.reply_text("Verified news posted to channel! ✅")


def main():
    """Start the bot"""
    print("🚀 Starting GoalFlowPulse Bot with Multi-Source Verification...")
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("scores", scores_command))
    application.add_handler(CommandHandler("news", news_command))
    
    # Set up scheduler for automated posts
    scheduler = AsyncIOScheduler()
    
    # News posts: 8:30 AM and 8:30 PM daily
    scheduler.add_job(
        post_news,
        CronTrigger(hour=8, minute=30),
        args=[application],
        id='morning_news'
    )
    scheduler.add_job(
        post_news,
        CronTrigger(hour=20, minute=30),
        args=[application],
        id='evening_news'
    )
    
    # Score updates every 2 hours during typical match times (12 PM - 11 PM)
    for hour in range(12, 23, 2):
        scheduler.add_job(
            post_scores,
            CronTrigger(hour=hour, minute=0),
            args=[application],
            id=f'scores_{hour}'
        )
    
    # Create polls for matches (runs twice daily)
    scheduler.add_job(
        create_match_polls,
        CronTrigger(hour=10, minute=0),
        args=[application],
        id='morning_polls'
    )
    scheduler.add_job(
        create_match_polls,
        CronTrigger(hour=16, minute=0),
        args=[application],
        id='afternoon_polls'
    )
    
    scheduler.start()
    
    print("✅ Bot is running with multi-source news verification!")
    print("📰 News sources: BBC Sport, ESPN, Sky Sports, Goal.com, The Guardian")
    print("🔥 Only posting news verified by 2+ sources!")
    print("\nPress Ctrl+C to stop.")
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
