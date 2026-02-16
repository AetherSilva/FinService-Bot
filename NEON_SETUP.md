# Neon PostgreSQL Integration Guide

This guide provides step-by-step instructions for setting up FinService-Bot with **Neon**, a serverless PostgreSQL database hosted in the cloud.

## Overview

- **Database**: PostgreSQL (via Neon)
- **Fallback**: Automatic SQLite fallback if PostgreSQL unavailable
- **Cost**: Free tier available (5 GB storage, 3GiB computation/month)
- **Setup Time**: 5-10 minutes

## Architecture

```
FinService-Bot
├── main.py (web bot)
├── bot.py (admin bot)
├── schedular.py (background worker)
└── db_layer_universal.py ← Auto-detects DATABASE_URL
    ├── PostgreSQL (if DATABASE_URL set)
    └── SQLite fallback
```

## Prerequisites

- Python 3.8+
- Neon account (free at https://console.neon.tech)
- PostgreSQL drivers installed (already in requirements.txt)

## Step 1: Create Neon Account

1. Visit https://console.neon.tech/auth/signup
2. Sign up with email or GitHub
3. Verify your email
4. Create a new project (default settings OK)

## Step 2: Get Connection String

### Via Neon Dashboard

1. Log in to https://console.neon.tech
2. Navigate to **Projects** → **Your Project**
3. Click **Databases** → **neondb**
4. Click **Connection details** (top right)
5. Copy the connection string under "Direct connection"

Format should look like:
```
postgresql://username:password@host/neondb
```

### Via Neon CLI (Optional)

```bash
# Install Neon CLI
npm install -g neonctl

# Authenticate
neonctl auth

# List projects
neonctl projects list

# Get connection string
neonctl databases list --project-id <project-id>
```

## Step 3: Configure .env File

Add to your `.env` file:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321
SESSION_SECRET=your_session_secret

# Neon PostgreSQL Configuration
DATABASE_URL=postgresql://username:password@your-neon-host/neondb

# Optional: SQLite fallback path (uses memory if not set)
SQLITE_PATH=backup.db
```

⚠️ **Security Note**: 
- Never commit `.env` to Git
- Add `.env` to `.gitignore`
- Rotate password if compromised

## Step 4: Test the Connection

Run the database test suite:

```bash
# Test with SQLite (default)
python test_db_universal.py

# Test with PostgreSQL
export DATABASE_URL="postgresql://user:pass@host/db"
python test_db_universal.py
```

Expected output:
```
✅ PASS: Database Type Detection
✅ PASS: Connection
✅ PASS: Tables Created
✅ PASS: Offer Insertion
... (10/10 tests pass)
```

## Step 5: Deploy with PostgreSQL

### Local Testing

```bash
# Set DATABASE_URL
export DATABASE_URL="postgresql://..."

# Run bot with PostgreSQL
python main.py
```

Watch for log message:
```
✓ PostgreSQL database layer initialized
```

### Deploy to Render.com

1. Update `render.yaml`:

```yaml
services:
  - type: web
    name: fin-service-bot
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python main.py"
    envVars:
      - key: TELEGRAM_BOT_TOKEN
        fromSecret: TELEGRAM_BOT_TOKEN
      - key: ADMIN_IDS
        fromSecret: ADMIN_IDS
      - key: DATABASE_URL
        fromSecret: DATABASE_URL
```

2. Add Render secrets in dashboard:
   - `TELEGRAM_BOT_TOKEN`
   - `ADMIN_IDS`
   - `DATABASE_URL` (from Neon)

3. Push to GitHub and deploy

### Deploy to Heroku

```bash
# Login
heroku login

# Create app
heroku create your-app-name

# Set environment variables
heroku config:set DATABASE_URL="postgresql://..."
heroku config:set TELEGRAM_BOT_TOKEN="..."

# Deploy
git push heroku main
```

## Step 6: Monitor and Maintain

### Check Database Status

```bash
# View database health
python test_db_universal.py

# View logs
# Render: Dashboard → Logs
# Heroku: heroku logs -t
```

### Neon Console Features

1. **Metrics**: View CPU, storage, queries
2. **Query Performance**: Analyze slow queries
3. **Backups**: Automatic daily backups
4. **Branches**: Create development databases

### Monitor Using MCP Server

```bash
# Start MCP server
python mcp_server.py

# In another terminal, query health
echo '{"tool": "health_check"}' | python mcp_server.py
```

## Troubleshooting

### Connection Timeout

**Error**: `psycopg2.OperationalError: could not connect to server`

**Solution**:
1. Verify DATABASE_URL is correct
2. Check Neon project is running (dashboard)
3. Check network connectivity
4. Falls back to SQLite automatically

```python
# In logs, you'll see:
# ⚠ PostgreSQL connection failed: ..., using SQLite
```

### Empty Database Tables

The `db_layer_universal.py` automatically creates tables on first connection:

- `users` - User registration and blocking
- `offers` - Service offers queued for posting
- `posting_history` - Posting results and timestamps

### Upgrade Neon Plan

If exceeding free tier (5 GB storage, 3 GiB compute/month):

1. Neon Dashboard → **Billing**
2. Choose **Pro** or **Business** plan
3. Automatic upgrade, no downtime

## Advanced Configuration

### Connection Pooling

For Render/Heroku, enable PgBouncer:

```bash
# In .env
DATABASE_URL="postgresql://user:pass@host/neondb?sslmode=require"

# Add pgbouncer endpoint (if using Neon Pro)
DATABASE_URL="postgresql://user:pass@pgbouncer-host/neondb"
```

### Custom Schema

To modify database schema:

```python
# In db_layer_universal.py
# Modify _create_postgres_tables() or _create_tables() in __init__
```

Run migration:

```bash
python -c "from db_layer_universal import db_manager; db_manager.init_db()"
```

### Backups

Neon Pro includes:
- 7-day retention on free plan
- 30-day retention on Pro
- Manual backup via branching

## Performance Tips

1. **Indexes**: Database auto-creates indexes on:
   - `offers(service_type, status)`
   - `users(user_id)`

2. **Query Optimization**: Use `limit()` in production
   ```python
   offers = db_manager.next_queued_by_service(ServiceType.CREDIT_CARD)
   ```

3. **Monitor Logs**:
   ```bash
   # Via Neon Dashboard → Settings → Logs
   ```

## Fallback Strategy

The `db_layer_universal.py` implements automatic fallback:

```
Try PostgreSQL (via DATABASE_URL)
    ↓
If fails, fallback to SQLite
    ↓
Both databases share same schema
    ↓
Zero application code changes
```

## Cost Estimation

| Feature | Free Tier | Pro |
|---------|-----------|-----|
| Storage | 5 GB | 100 GB |
| Compute | 3 GiB/month | Unlimited |
| Databases | 1 | Unlimited |
| Backups | 1 day | 7 days |
| Cost | $0 | $15/month |

For FinService-Bot:
- ~50 offers/day = ~1.5 MB/month storage
- Free tier easily sufficient

## Next Steps

1. ✅ Create Neon account and project
2. ✅ Get DATABASE_URL connection string
3. ✅ Add to .env file
4. ✅ Run `test_db_universal.py` to verify
5. ✅ Deploy to Render/Heroku with DATABASE_URL
6. ✅ Monitor via Neon dashboard or MCP server

## Support

- **Neon Docs**: https://neon.tech/docs
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **This Project**: See README.md

## Security Checklist

- [ ] DATABASE_URL added to .env
- [ ] .env added to .gitignore
- [ ] No hardcoded credentials in code
- [ ] Deployment secrets configured
- [ ] Connection string uses SSL (`?sslmode=require`)
- [ ] Password changed after first login
- [ ] Regular backups enabled

---

**Last Updated**: 2024
**Status**: ✅ Complete and Tested
