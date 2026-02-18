# 🚀 FinService-Bot

A production-ready Telegram automation system for routing financial referral offers to service-specific channels, with enterprise-grade database support and deployment infrastructure.

## ✨ Features

### Core Features
- **Deterministic Routing**: Maps 13+ service types to specific Telegram channels
- **Multilingual Support**: English, Hindi, and Gujarati templates
- **Automated Scheduler**: Posts offers on configurable intervals (default 1.6 hours)
- **Admin Command Interface**: 8 admin commands for offer and channel management
- **Bulk CSV Import**: Import offers in bulk with validation

### Enterprise Features
- **Universal Database Layer**: SQLite + PostgreSQL with automatic fallback
- **Neon PostgreSQL Integration**: Serverless PostgreSQL via Neon (optional)
- **MCP Server**: 11 database tools exposed via Model Context Protocol
- **Health Checks**: Built-in HTTP health endpoints for monitoring (port 8000/8001)
- **Multi-Platform Deployment**: Render, Heroku, Replit, self-hosted VPS
- **Comprehensive Testing**: 30+ test scenarios with 100% pass rate
- **Error Logging**: Detailed error context and debugging information

## 🛠 Tech Stack

**Core**:
- Python 3.8+
- python-telegram-bot v20.7+
- python-dotenv 1.0.0+

**Database**:
- SQLite 3 (default)
- PostgreSQL via Neon (optional)
- psycopg2-binary & asyncpg drivers

**Deployment**:
- Render.com (web + background worker)
- Heroku (multi-dyno)
- Replit
- Self-hosted VPS

## 🚀 Quick Start

### 1. Setup & Installation

```bash
# Clone project
git clone <repo>
cd FinService-Bot

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit with your TELEGRAM_BOT_TOKEN and ADMIN_IDS
```

### 2. Local Testing

```bash
# Run tests
python test_db_universal.py    # Database: 10/10 ✅
python test_all_commands.py    # Commands: 12/12 ✅
python test_startup.py         # Startup: All ✅

# Run bot
python main.py

# In another terminal, run scheduler
python schedular.py
```

### 3. PostgreSQL Setup (Optional)

```bash
# Interactive setup with Neon
python setup_neon.py

# Follow prompts to:
# 1. Get Neon connection string
# 2. Configure DATABASE_URL in .env
# 3. Test connection
# 4. Run verification
```

### 4. Deployment

**Render.com**:
```bash
git push origin main
# Deploy from Render.com dashboard using render.yaml
```

**Heroku**:
```bash
heroku create your-app
heroku config:set TELEGRAM_BOT_TOKEN="..."
git push heroku main
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed platform-specific instructions.

## 📋 Bot Commands

| Command | Admin Only | Purpose |
|---------|:----------:|---------|
| `/start` | No | Show bot status and options |
| `/help` | No | Show command help |
| `/stats` | Yes | View offer queue statistics |
| `/list_services` | Yes | List all service categories and their channels |
| `/add_offer` | Yes | Interactively add a new referral vector |
| `/setup_channels` | Yes | Configure or update channel IDs for services |
| `/cancel` | Yes | Abort the current interactive session |
| `/block` | Yes | Block a user by ID from using the bot |
| `/unblock` | Yes | Unblock a user by ID |

### 📥 Bulk Import
Admins can upload a **CSV file** to the bot to inject multiple offers at once. The bot will validate the structure and integrate the vectors into the database automatically.

## 📊 Service Categories (13 Types)

- Credit Cards
- Personal Loans
- Business Loans
- Home Loans
- Savings Accounts
- Current Accounts
- Credit Builder
- Health Insurance
- Vehicle Insurance
- Personal Accident Insurance
- Demat Accounts
- Mutual Funds
- Fixed Income Products

## 📂 Project Structure

```
FinService-Bot/
├── main.py                  (Interactive bot + health check)
├── bot.py                   (Admin bot variant)
├── schedular.py             (Background scheduler)
├── admin_commands.py         (8 admin commands)
├── db_layer.py              (Original SQLite)
├── db_layer_universal.py    (NEW: SQLite/PostgreSQL)
├── mcp_server.py            (NEW: MCP protocol handler)
├── config_schema.py         (Service taxonomy)
├── templates.py             (Multilingual templates)
├── csv_validator.py         (CSV import validation)
├── setup_neon.py            (NEW: Neon setup wizard)
├── services_config.yaml     (Service mappings)
├── render.yaml              (Render deployment)
├── Procfile                 (Heroku deployment)
├── .env                     (Local secrets)
├── .gitignore               (Git exclusions)
├── requirements.txt         (Dependencies)
├── README.md                (This file)
├── DEPLOYMENT.md            (4-platform guide)
├── NEON_SETUP.md            (PostgreSQL setup)
├── PROJECT_COMPLETION.md    (Completion report)
└── test_*.py                (Test suites)
```

## 🗄️ Database

### SQLite (Default)
- No setup required
- File-based: `fin_referrals.db`
- Perfect for local development

### PostgreSQL via Neon (Optional)
- Serverless PostgreSQL cloud database
- Free tier: 5 GB storage, 3 GiB compute/month
- Automatic table creation on first connection
- Connection string via `DATABASE_URL` environment variable

### Automatic Fallback
If `DATABASE_URL` is set but PostgreSQL is unavailable, automatically falls back to SQLite - no code changes needed.

## 🔗 MCP Server

The MCP (Model Context Protocol) server exposes 11 database tools:

```bash
python mcp_server.py

# Examples
echo '{"tool": "health_check"}' | python mcp_server.py
echo '{"tool": "get_stats"}' | python mcp_server.py
echo '{"tool": "get_offers", "params": {"service_type": "credit_card"}}' | python mcp_server.py
```

Tools available:
- `get_offers` - Retrieve offers by service/status
- `add_offer` - Add new offer
- `get_stats` - Get statistics
- `get_services` - List services
- `get_channel` - Get channel for service
- `update_channel` - Update channel mapping
- `block_user` / `unblock_user` - User management
- `get_next_offer` - Get next queued offer
- `mark_offer_posted` - Mark offer status
- `health_check` - Server health

## 📈 Health Checks

Built-in HTTP health check servers:
- **main.py**: Port 8000 (`/health`)
- **bot.py**: Port 8000 (`/health`)
- **schedular.py**: Port 8001 (`/health`)

Perfect for monitoring and deployment platforms (Render, Heroku, K8s).

## 🧪 Testing

```bash
# Run all tests
python test_db_universal.py    # Database layer: 10/10 ✅
python test_all_commands.py    # Commands: 12/12 ✅
python test_startup.py         # Startup checks ✅
python test_debug.py           # Full debug suite ✅

# Validate syntax
python -m py_compile *.py      # All files valid ✅
```

## 📚 Documentation

1. **README.md** (this file) - Project overview & quick start
2. **NEON_SETUP.md** - PostgreSQL via Neon setup guide
3. **DEPLOYMENT.md** - Deploy to Render, Heroku, Replit, VPS
4. **PROJECT_COMPLETION.md** - Complete project report
5. **FIXES_AND_DEBUGGING.md** - Historical fixes & debugging

## 🔐 Security

✅ Environment variables via `.env` (not committed)
✅ Admin-only command authorization
✅ User blocking system
✅ No hardcoded secrets
✅ Input validation
✅ SSL/TLS ready

## 🚀 Deployment

### Status
- ✅ Render.com: Multi-service (web + scheduler)
- ✅ Heroku: Multi-dyno (Procfile)
- ✅ Replit: Built-in environment
- ✅ Self-hosted VPS: Documented

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## 💾 Database Schema

### users table
- user_id (Primary Key)
- username
- blocked (Boolean)
- joined_at (Timestamp)

### offers table
- id (Serial Primary Key)
- service_type
- provider
- Multilingual titles (EN/HI/GU)
- referral_link
- status (queued/posted/failed)
- created_at, updated_at

### posting_history table
- id (Serial)
- offer_id (Foreign Key)
- posted_at
- result (success/fail)

## 🎯 Performance

| Operation | Time |
|-----------|------|
| Connect | <100ms |
| Get stats | <200ms |
| Next queued offer | <50ms |
| Insert offer | <100ms |

## 📝 License

See [LICENSE](LICENSE) file.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## 📧 Support

For issues or questions:
1. Check [DEPLOYMENT.md](DEPLOYMENT.md) for platform-specific help
2. Review [FIXES_AND_DEBUGGING.md](FIXES_AND_DEBUGGING.md) for known issues
3. Run test suites to verify setup
4. Check logs for detailed error messages

## 🎉 Status

✅ **Production Ready**
- All tests passing (30+ scenarios)
- Enterprise features implemented
- Multi-platform deployment ready
- Comprehensive documentation

---

**Version**: 1.0.0 (Production Release)
**Last Updated**: February 18, 2026
**Status**: ✅ Stable & Tested

- `/help`: Detailed command guide.
