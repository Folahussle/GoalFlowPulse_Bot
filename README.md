# GoalFlowPulse — Telegram Football Bot

## What this does (very simple)
This bot posts live football scores and top news/transfer roundups to your Telegram channel automatically.

## Files to add
- requirements.txt
- utils.py
- db_utils.py
- news_fetcher.py
- bot.py
- .github/workflows/main.yml

## Before you push (important)
1. Create a Telegram bot with BotFather and a public channel `@GoalFlowPulse`.
2. Add the bot as an admin to the channel.
3. Sign up at Football-Data.org and get your free API token.
4. (Optional) Sign up at NewsAPI.org for extra news coverage.

## Add secrets on GitHub
Go to **Settings → Secrets and variables → Actions** and add:
- `FOOTBALL_API_KEY` = your football-data token
- `TELEGRAM_TOKEN` = your BotFather token
- `CHANNEL_ID` = @GoalFlowPulse
- `NEWSAPI_KEY` = (optional)

## How to test locally
1. Create a `.env` file (do not commit) with the same keys.
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python bot.py` (posts live scores)
4. Run: `COMMAND=news python bot.py` (posts news)

## Go live
Push to GitHub. In Actions, run the workflow manually once to ensure it works. The scheduler will run automatically after that.