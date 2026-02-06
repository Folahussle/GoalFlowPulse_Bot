# GoalFlowPulse — Telegram Football Bot

## What it does
- Posts HALFTIME and FULL‑TIME messages for priority competitions.
- Posts top news & transfer roundups twice daily.
- Avoids reposting the same event using a small SQLite DB.

## How to set up
1. Create a Telegram bot with BotFather and a public channel (e.g., @GoalFlowPulse). Add bot as admin.
2. Get Football-Data.org API key.
3. Create a GitHub repo and add these files.
4. Add GitHub Secrets: `FOOTBALL_API_KEY`, `TELEGRAM_TOKEN`, `CHANNEL_ID`, `NEWSAPI_KEY` (optional).
5. Push to GitHub. Actions will run automatically.

## Edit
All behavior (timing, message text, leagues) is editable in the Python files in this repo.