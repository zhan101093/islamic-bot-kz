# 🕌 Islamic AI Education Bot

Telegram боты — Қазақ тілінде ұстаздарға арналған күнделікті AI кеңестерін каналға жіберетін бот.

---

## 📁 Project Structure

```
telegram_bot/
├── bot.py              # Main bot code
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── .env                # Your actual secrets (never commit!)
├── Procfile            # For Render/Railway deployment
├── runtime.txt         # Python version
├── post_history.json   # Auto-created: tracks sent topics
└── bot.log             # Auto-created: logs
```

---

## 🚀 LOCAL SETUP (Step by Step)

### Step 1 — Get API Keys

**Telegram Bot Token:**
1. Open Telegram → search `@BotFather`
2. Send `/newbot`
3. Choose a name and username
4. Copy the token (looks like `7123456789:AAF...`)

**IMPORTANT — Add bot to channel:**
1. Open your Telegram channel settings
2. Administrators → Add Administrator
3. Search your bot username → Add
4. Give it "Post Messages" permission

**Google Gemini API Key:**
1. Go to https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key

---

### Step 2 — Install Python 3.11+

Check: `python --version`

If not installed: https://www.python.org/downloads/

---

### Step 3 — Clone / Download project

```bash
# If using git:
git clone <your-repo-url>
cd telegram_bot

# Or just put all files in a folder named telegram_bot
```

---

### Step 4 — Create virtual environment

```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

---

### Step 5 — Install dependencies

```bash
pip install -r requirements.txt
```

---

### Step 6 — Create your .env file

```bash
# Copy the example
cp .env.example .env
```

Open `.env` in any text editor and fill in:

```env
TELEGRAM_TOKEN=7123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
CHANNEL_ID=-1003903707711
POST_HOUR=9
POST_MINUTE=0
```

---

### Step 7 — Run the bot

```bash
python bot.py
```

You should see:
```
2025-01-15 08:00:00 | INFO | Scheduler started — posts at 09:00 daily
2025-01-15 08:00:00 | INFO | Bot is running...
```

---

### Step 8 — Test it

Open Telegram, find your bot, send:
- `/start` — welcome message
- `/post` — send a post RIGHT NOW to the channel
- `/history` — last 10 topics
- `/status` — bot info

---

## ☁️ DEPLOYMENT ON RENDER (Free)

### Step 1 — Push to GitHub

```bash
git init
git add .
# IMPORTANT: make sure .env is in .gitignore!
echo ".env" >> .gitignore
echo "*.log" >> .gitignore
echo "post_history.json" >> .gitignore
git commit -m "Initial bot"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### Step 2 — Create Render account

Go to https://render.com → Sign up with GitHub

### Step 3 — Create new Background Worker

1. Dashboard → **New** → **Background Worker**
2. Connect your GitHub repo
3. Settings:
   - **Name:** `islamic-ai-bot`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`

### Step 4 — Add Environment Variables

In Render dashboard → **Environment** tab, add:

| Key | Value |
|-----|-------|
| `TELEGRAM_TOKEN` | your token |
| `GEMINI_API_KEY` | your key |
| `CHANNEL_ID` | `-1003903707711` |
| `POST_HOUR` | `9` |
| `POST_MINUTE` | `0` |

### Step 5 — Deploy

Click **Deploy** → Wait 2-3 minutes → Bot is live!

⚠️ **Note on Render free tier:** Free background workers sleep after inactivity. 
For a persistent bot, use the $7/month Starter plan, or use Railway instead.

---

## ☁️ DEPLOYMENT ON RAILWAY (Recommended)

### Step 1 — Create Railway account

Go to https://railway.app → Login with GitHub

### Step 2 — New Project

1. **New Project** → **Deploy from GitHub repo**
2. Select your repository

### Step 3 — Add Environment Variables

Go to your service → **Variables** tab → Add all 5 variables from the table above

### Step 4 — Set Start Command

Go to **Settings** → **Deploy** → Start Command:
```
python bot.py
```

### Step 5 — Deploy

Railway auto-deploys on every push to main. Your bot runs 24/7.

Free tier: $5/month credit (usually enough for a small bot).

---

## 🕐 TIMEZONE NOTE

The `POST_HOUR` uses the **server's local time**.

- **Render/Railway** servers are in UTC by default
- Almaty is **UTC+5**
- So if you want 09:00 Almaty time → set `POST_HOUR=4` (UTC)

To force a specific timezone on Railway, add:
```
TZ=Asia/Almaty
```
as an environment variable — then `POST_HOUR=9` will work correctly.

---

## 🛠 COMMANDS REFERENCE

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/post` | Send a post manually right now |
| `/history` | Show last 10 used topics |
| `/status` | Show bot status and stats |

---

## 🔧 CUSTOMIZATION

**Change posting time:**
Edit `.env`:
```
POST_HOUR=8   # 8:00 AM
POST_MINUTE=30  # 8:30 AM
```

**Add more topics:**
Edit `TOPIC_SEEDS` list in `bot.py` — add as many as you want.

**Change post language/style:**
Edit `SYSTEM_PROMPT` and `POST_TEMPLATE` strings in `bot.py`.

---

## 📋 TROUBLESHOOTING

**"Chat not found" error:**
→ Make sure bot is added as Admin to the channel with posting rights

**"Unauthorized" error:**
→ Check your `TELEGRAM_TOKEN` is correct

**Gemini errors:**
→ Check `GEMINI_API_KEY` and that the Generative AI API is enabled in Google Cloud

**Posts not sending at scheduled time:**
→ Check timezone. Add `TZ=Asia/Almaty` to environment variables.

---

## 📄 .gitignore (recommended)

```
.env
*.log
post_history.json
venv/
__pycache__/
*.pyc
```
