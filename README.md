# ⚽ GoalFlowPulse - Football Telegram Bot

A Nigerian-vibes football bot that posts news, scores, and creates match polls for your Telegram channel!

## 🌟 Features

✅ **Automated News Posts** - Twice daily (8:30 AM & 8:30 PM)  
✅ **Live Scorelines** - Updates every 2 hours during match times  
✅ **Match Polls** - Fans vote on predictions, results posted 10 mins before kickoff  
✅ **Nigerian Vibe** - All messages with authentic Naija flavor! 🔥  
✅ **Major Leagues Coverage** - EPL, La Liga, Serie A, Bundesliga, Ligue 1, Champions League  

---

## 📚 Step-by-Step Setup (Easy as ABC!)

### Step 1: Get Your Computer Ready

**What is this?** We need to prepare your computer to run the bot.

**For Windows:**
1. Download Python from https://www.python.org/downloads/
2. Click "Download Python" (the big yellow button)
3. Run the installer
4. ⚠️ **IMPORTANT**: Check the box "Add Python to PATH"
5. Click "Install Now"

**For Mac:**
1. Open Terminal (search for "Terminal" in Spotlight)
2. Copy and paste: `brew install python3`
3. Press Enter

**For Linux:**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

---

### Step 2: Download the Bot Files

**What is this?** Getting the bot code onto your computer.

**Option A - Using GitHub (Recommended):**
1. Go to https://github.com (create account if you don't have one)
2. Click the green "New" button to create a repository
3. Name it "GoalFlowPulse-Bot"
4. Click "Create repository"
5. Click "uploading an existing file"
6. Upload all the bot files (bot.py, requirements.txt, .env.example)
7. Click "Commit changes"

**To download to your computer:**
1. Click the green "Code" button
2. Click "Download ZIP"
3. Unzip the folder on your computer

**Option B - Manual Download:**
1. Create a new folder on your computer called "GoalFlowPulse"
2. Put all the bot files inside (bot.py, requirements.txt, .env.example)

---

### Step 3: Install the Bot's Tools

**What is this?** Installing the special programs the bot needs to work.

1. Open Terminal (Mac/Linux) or Command Prompt (Windows)
2. Navigate to your bot folder:
   ```bash
   cd path/to/GoalFlowPulse
   ```
   (Replace "path/to/GoalFlowPulse" with where you saved the folder)

3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
   
   Or if that doesn't work, try:
   ```bash
   pip3 install -r requirements.txt
   ```

**What's happening?** Your computer is downloading helper programs the bot needs!

---

### Step 4: Set Up Your Secret Keys

**What is this?** Telling the bot your personal information.

1. In your GoalFlowPulse folder, create a new file called `.env`
2. Copy everything from `.env.example` into `.env`
3. Your `.env` file should look like this:

```
TELEGRAM_BOT_TOKEN=8542955893:AAHfwn30QcJjHpJ_Ck-gZCYR9M7BzS7BK94
FOOTBALL_API_KEY=773af02a0f5b4096908a2caa5d225dae
CHANNEL_NAME=@GoalFlowPulse
```

**On Windows:** 
- Open Notepad
- Save as `.env` (with the dot at the start!)
- When saving, change "Save as type" to "All Files"

**On Mac/Linux:**
```bash
cp .env.example .env
```

---

### Step 5: Make Your Bot Admin of Your Channel

**What is this?** Giving the bot permission to post in your channel.

1. Open Telegram
2. Go to your channel @GoalFlowPulse
3. Click on the channel name at the top
4. Click "Administrators"
5. Click "Add Administrator"
6. Search for your bot (search for the name you gave it when creating with BotFather)
7. Give it these permissions:
   - ✅ Post messages
   - ✅ Edit messages  
   - ✅ Delete messages
   - ✅ Create polls
8. Click "Done"

---

### Step 6: Run Your Bot!

**What is this?** Starting your bot so it comes alive!

1. Open Terminal/Command Prompt
2. Make sure you're in the GoalFlowPulse folder
3. Type this command:
   ```bash
   python bot.py
   ```
   
   Or if that doesn't work:
   ```bash
   python3 bot.py
   ```

**You should see:**
```
🚀 Starting GoalFlowPulse Bot...
✅ Bot is running! Press Ctrl+C to stop.
```

**Congratulations!** Your bot is now running! 🎉

---

### Step 7: Test Your Bot

1. Go to your Telegram channel @GoalFlowPulse
2. Wait a few minutes
3. You should see posts appearing!

**Manual test:**
- Send `/start` to your bot in a private message
- It should reply with a welcome message!

---

## 🚀 Keeping Your Bot Running 24/7

**Problem:** When you close your computer, the bot stops!

**Solution:** Use a cloud service to run it non-stop.

### Option 1: PythonAnywhere (FREE & Easy!)

1. Go to https://www.pythonanywhere.com
2. Sign up for a free account
3. Click "Open Bash console"
4. Clone your GitHub repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/GoalFlowPulse-Bot.git
   cd GoalFlowPulse-Bot
   ```
5. Install requirements:
   ```bash
   pip install --user -r requirements.txt
   ```
6. Create your .env file:
   ```bash
   nano .env
   ```
7. Paste your credentials, press Ctrl+X, then Y, then Enter
8. Run the bot:
   ```bash
   python bot.py
   ```

**To keep it running forever:**
- Go to "Tasks" tab
- Add a new scheduled task
- Command: `python /home/YOUR_USERNAME/GoalFlowPulse-Bot/bot.py`
- Frequency: Daily

### Option 2: Heroku (Paid but powerful)

1. Create account at https://heroku.com
2. Install Heroku CLI
3. In your bot folder:
   ```bash
   git init
   heroku create goalflowpulse-bot
   git add .
   git commit -m "Initial commit"
   git push heroku main
   ```

### Option 3: AWS/Digital Ocean/Google Cloud

More advanced - follow their Python deployment guides!

---

## 📱 Bot Commands

Users can interact with your bot using these commands:

- `/start` - Welcome message
- `/help` - Show all commands  
- `/scores` - Get latest scores manually
- `/news` - Get football news
- `/upcoming` - See upcoming matches

---

## ⚙️ Customization Tips

### Change Posting Times

In `bot.py`, find these lines:
```python
scheduler.add_job(
    post_news,
    CronTrigger(hour=8, minute=30),  # Change 8 to different hour
    args=[application],
    id='morning_news'
)
```

### Add More Nigerian Phrases

Find the `NIGERIAN_VIBES` list and add your own:
```python
NIGERIAN_VIBES = [
    "🔥 E don set! ",
    "⚡ Your own phrase here! ",
    # Add more...
]
```

### Add More Leagues

In the `MAJOR_LEAGUES` dictionary, add:
```python
'SPL': {'id': 2017, 'name': 'Saudi Pro League', 'emoji': '🇸🇦'},
```

---

## 🐛 Troubleshooting

### Bot not posting?
- ✅ Check bot is admin in channel
- ✅ Make sure channel username is correct (@GoalFlowPulse)
- ✅ Verify your tokens are correct in .env file

### "Module not found" error?
```bash
pip install -r requirements.txt --force-reinstall
```

### API rate limit exceeded?
- Football-data.org free tier has limits
- Wait 1 minute between requests
- Consider upgrading API plan

### Bot stops after closing terminal?
- Use PythonAnywhere, Heroku, or similar service
- Or use `nohup python bot.py &` on Linux

---

## 🎯 Suggestions for Improvement

1. **🎥 Video Highlights** - Integrate with YouTube API to share goal clips
2. **📈 Player Stats** - Show top scorers, assists leaders
3. **🏆 League Tables** - Post standings weekly
4. **⏰ Match Reminders** - Notify subscribers 1 hour before big games
5. **🎲 Fantasy Football** - Create mini fantasy league in channel
6. **📊 Head-to-Head Stats** - Historical data before matches
7. **💬 Match Threads** - Live commentary during games
8. **🌍 Transfer Window Tracker** - Special posts during transfer windows
9. **🗞️ Quotes & Interviews** - Post manager/player quotes
10. **🎪 Memes & Banter** - Nigerian football memes after big moments!

---

## 📋 File Structure

```
GoalFlowPulse-Bot/
│
├── bot.py              # Main bot code
├── requirements.txt    # Python packages needed
├── .env.example       # Example environment file
├── .env               # Your actual secrets (DON'T share!)
├── README.md          # This file!
└── .gitignore         # Files to ignore in Git
```

---

## 🔐 Security Tips

⚠️ **NEVER share your .env file!**  
⚠️ **NEVER commit .env to GitHub!**  
⚠️ **Keep your bot token private!**

Create `.gitignore` file with:
```
.env
__pycache__/
*.pyc
```

---

## 📞 Support

Having issues? Here's what to do:

1. Check the error message carefully
2. Google the error (usually someone else had it!)
3. Check Telegram Bot API docs: https://core.telegram.org/bots/api
4. Check Football-data.org docs: https://www.football-data.org/documentation

---

## 📜 License

Free to use! Share with your friends! ⚽🔥

---

## 🙏 Credits

Built with:
- Python 🐍
- python-telegram-bot 🤖
- Football-data.org API ⚽
- Nigerian vibes 🇳🇬💯

---

**E don set! Your football channel go dey lit! 🔥⚽**

Questions? Your bot is ready to ball! Just follow the steps slowly and you go make am! 💪
