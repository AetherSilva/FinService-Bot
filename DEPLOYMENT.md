# FinService-Bot Deployment Guide

## Quick Start

### Prerequisites
- Python 3.8+
- Telegram Bot Token (from @BotFather)
- Telegram User IDs for admin access
- Internet connection

### Local Development

```bash
# 1. Clone the repository
git clone https://github.com/AetherSilva/FinService-Bot.git
cd FinService-Bot

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cat > .env << EOF
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
ADMIN_IDS=YOUR_USER_ID_HERE,ANOTHER_ADMIN_ID
SESSION_SECRET=$(python -c 'import secrets; print(secrets.token_urlsafe(48))')
EOF

# 5. Run verification tests
python test_startup.py      # Quick check (30 seconds)
python test_all_commands.py # Comprehensive test (2 minutes)

# 6. Start the bot
python main.py              # Interactive mode
# OR
python bot.py               # Admin mode
# OR
python schedular.py --continuous --interval 1.6  # Scheduler only
```

## Deployment Platforms

### 1. **Render.com** (Recommended)

**Advantages:**
- Free tier available
- Easy GitHub integration
- Background workers for scheduler
- Built-in environment variables

**Setup Steps:**

1. **Connect GitHub Repository**
   - Go to https://render.com
   - Sign up/login with GitHub
   - Click "New+" → "Web Service"
   - Select your FinService-Bot repository

2. **Configure Main Bot Service**
   - **Name:** `finservice-bot-api`
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`

3. **Add Environment Variables**
   ```
   TELEGRAM_BOT_TOKEN=your_token_here
   ADMIN_IDS=12345,67890
   SESSION_SECRET=generate_random_string
   ```

4. **Create Background Worker Service**
   - Click "New+" → "Background Worker"
   - **Name:** `finservice-bot-scheduler`
   - **Repository:** Same as above
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python schedular.py --continuous --interval 1.6`

5. **Set Same Environment Variables**
   - Add TELEGRAM_BOT_TOKEN
   - Add any database URLs if needed

**Monitoring:**
- Render dashboard shows logs in real-time
- Restart services if needed from dashboard
- Monitor resource usage

### 2. **Replit**

**Setup Steps:**

1. **Create New Replit**
   - Go to https://replit.com
   - Click "Create Replit"
   - Choose "Import from GitHub"
   - Paste: `https://github.com/AetherSilva/FinService-Bot`

2. **Configure Environment Variables**
   - Click "Secrets" (lock icon)
   - Add:
     ```
     TELEGRAM_BOT_TOKEN=your_token_here
     ADMIN_IDS=12345,67890
     SESSION_SECRET=random_string
     ```

3. **Create Run Configuration**
   - Click "Run" or use command: `python main.py`

4. **Keep Alive (Optional)**
   - Use Uptime Robot to ping the service regularly
   - Prevents Replit from stopping idle projects

### 3. **Heroku** (Legacy, but still works)

**Setup with Procfile:**

```
web: python main.py
scheduler: python schedular.py --continuous --interval 1.6
```

**Deploy:**
```bash
heroku login
git push heroku main
heroku config:set TELEGRAM_BOT_TOKEN=your_token
```

### 4. **Self-Hosted (VPS/Server)**

**Requirements:**
- Ubuntu 20.04+ or similar Linux
- SSH access
- systemd for process management

**Installation:**

```bash
# 1. SSH into server
ssh user@your.server.ip

# 2. Install dependencies
sudo apt update
sudo apt install python3.9 python3.9-venv git

# 3. Clone repository
git clone https://github.com/AetherSilva/FinService-Bot
cd FinService-Bot

# 4. Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# 5. Install Python dependencies
pip install -r requirements.txt

# 6. Create .env file with secrets
nano .env
# Add your credentials

# 7. Create systemd service file
sudo nano /etc/systemd/system/finservice-bot.service
```

**Systemd Service File:**

```ini
[Unit]
Description=FinService Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/your_username/FinService-Bot
Environment="PATH=/home/your_username/FinService-Bot/venv/bin"
ExecStart=/home/your_username/FinService-Bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and Start:**

```bash
sudo systemctl enable finservice-bot
sudo systemctl start finservice-bot
sudo systemctl status finservice-bot
```

## Environment Variables

| Variable | Required | Example | Purpose |
|----------|----------|---------|---------|
| `TELEGRAM_BOT_TOKEN` | ✅ Yes | `8073736875:AAF76OXex...` | Bot authentication |
| `ADMIN_IDS` | ✅ Yes | `123456,789012` | Admin user access |
| `SESSION_SECRET` | ❌ Optional | Random string | Session encryption |

**Generate Random Secret:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Verification Checklist

- [ ] Bot token obtained from @BotFather
- [ ] Admin user IDs collected
- [ ] `.env` file created with credentials
- [ ] `python test_startup.py` passes
- [ ] `python test_all_commands.py` shows 12/12 passed
- [ ] Bot added to all target channels
- [ ] Bot has admin permissions in channels
- [ ] Database file created (`fin_referrals.db`)
- [ ] Configuration file created (`services_config.yaml`)

## Troubleshooting

### "TELEGRAM_BOT_TOKEN not found"
```bash
# Check if .env exists
ls -la .env

# Check if token is set
grep TELEGRAM_BOT_TOKEN .env

# Load .env in current session
export $(cat .env | xargs)
python main.py
```

### "Bot doesn't receive messages"
1. Verify bot is added to the channel/group
2. Check bot has message sending permissions
3. Ensure admin user ID is correct
4. Review logs: `tail -f bot.log`

### "Database locked" error
- Ensure only one instance of bot/scheduler is running
- Stop all processes: `pkill -f python`
- Delete lock file if exists: `rm fin_referrals.db-wal`
- Restart: `python main.py`

### "No module named 'telegram'"
```bash
# Ensure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Verify installation
python -c "import telegram; print(telegram.__version__)"
```

## Monitoring

### Local Development
```bash
# View logs
tail -f bot.log

# Check database
sqlite3 fin_referrals.db "SELECT COUNT(*) FROM offers;"

# Monitor processes
watch -n 1 'ps aux | grep python'
```

### Render.com
- Logs visible in browser dashboard
- Real-time monitoring of resource usage
- Automatic restart on failure

### Self-Hosted
```bash
# View service logs
sudo journalctl -u finservice-bot -f

# Check service status
sudo systemctl status finservice-bot

# Restart service
sudo systemctl restart finservice-bot
```

## Scaling Considerations

**Single Instance:**
- Good for: Small deployments, testing
- Handles: ~100 messages/second

**Multi-Instance (with Load Balancer):**
- Database remains single SQLite file
- Each instance needs unique session storage
- Recommended: Use PostgreSQL instead of SQLite

**Scheduler Optimization:**
- Keep scheduler as separate worker process
- Interval: 1.6 hours (configurable)
- Can run multiple scheduler instances with load balancing

## Security Best Practices

1. **Never commit .env file**
   ```bash
   # Verify .gitignore
   cat .gitignore | grep ".env"
   ```

2. **Rotate bot token if compromised**
   - Generate new token at @BotFather
   - Update environment variables
   - Restart bot

3. **Use strong admin password**
   - Use random token for SESSION_SECRET
   - Change regularly

4. **Limit admin access**
   - Add only trusted user IDs to ADMIN_IDS
   - Remove compromised accounts immediately

5. **Database security**
   - Backup fin_referrals.db regularly
   - Keep in secure location
   - Use encryption for production

## Backup & Recovery

**Backup Database:**
```bash
# Local
cp fin_referrals.db backups/fin_referrals.db.$(date +%Y%m%d)

# Remote (to server)
scp fin_referrals.db user@server:/backups/
```

**Restore:**
```bash
# Stop the service
sudo systemctl stop finservice-bot

# Restore backup
cp backups/fin_referrals.db.20260215 fin_referrals.db

# Start service
sudo systemctl start finservice-bot
```

## Support & Issues

- 📖 Documentation: [README.md](README.md)
- 🐛 Bug Reports: GitHub Issues
- 📞 Contact: Use issues for questions
- 🔧 Debug: Run `python test_debug.py`

---

**Last Updated:** 2026-02-15  
**Version:** 1.0.0  
**Status:** Production Ready
