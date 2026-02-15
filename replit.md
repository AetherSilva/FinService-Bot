# FinReferrals Bot

## Overview

FinReferrals Bot is a Telegram automation system designed to route financial referral offers to service-specific channels. The bot manages a queue of financial offers (credit cards, loans, insurance, investments, etc.) and automatically posts them to designated Telegram channels on a scheduled basis.

Key capabilities:
- Deterministic routing of offers to service-category-specific Telegram channels
- Multilingual content support (English mandatory, Hindi and Gujarati optional)
- Automated posting scheduler (1.6-hour intervals)
- Admin interface for offer management via Telegram commands
- CSV bulk import for offer ingestion
- User management with blocking capabilities

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Structure

The system follows a modular architecture with clear separation of concerns:

| Module | Purpose |
|--------|---------|
| `bot.py` | Main Telegram bot application entry point, command routing |
| `schedular.py` | Autonomous posting engine with interval-based execution |
| `db_layer.py` | SQLite database abstraction layer |
| `admin_commands.py` | Admin command handlers and session management |
| `config_schema.py` | Service taxonomy, enums, and channel configuration |
| `templates.py` | Multilingual message template rendering |
| `csv_validator.py` | CSV import validation and parsing |

### Data Model

**Core Entities:**
- **Offers**: Queued referral offers with multilingual content, fingerprint-based deduplication, status tracking, and rotation indexing
- **Users**: Registered Telegram users with blocking capability

**Service Categories (ServiceType enum):**
Credit cards, personal/business/home loans, savings/current accounts, credit builders, health/vehicle/PA insurance, demat accounts, mutual funds, fixed income investments.

### Design Patterns

1. **Singleton Managers**: `db_manager`, `config_manager`, `template_engine` are instantiated as module-level singletons
2. **Session-based Interactions**: Admin commands use `user_sessions` dict to track multi-step command flows
3. **Callback-driven UI**: Telegram inline keyboards with callback query handling for interactive flows
4. **Fingerprint Deduplication**: Offers are deduplicated using content-based fingerprints

### Bot Command Flow

- `/start` - Entry point, shows available channels and admin commands if authorized
- `/add_offer` - Interactive multi-step offer creation
- `/setup_channels` - Configure channel IDs for each service category
- `/stats` - View queue statistics
- `/block` / `/unblock` - User management

### Scheduling Architecture

The scheduler (`schedular.py`) runs as a separate process, querying the database for pending offers and posting them via the Telegram Bot API. It operates independently from the main bot process.

## External Dependencies

### Telegram Bot API
- **Library**: `python-telegram-bot` v20+
- **Authentication**: Bot token from @BotFather via `BOT_TOKEN` or `TELEGRAM_BOT_TOKEN` environment variable
- **Requirements**: Bot must be added as administrator to all target channels

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `BOT_TOKEN` / `TELEGRAM_BOT_TOKEN` | Telegram Bot API token |
| `ADMIN_IDS` | Comma-separated Telegram user IDs for admin access |

### Database

- **Engine**: SQLite (file-based at `fin_referrals.db`)
- **Tables**: `offers`, `users`
- **Concurrency**: Uses `check_same_thread=False` for multi-thread access

### Python Dependencies

```
python-telegram-bot>=20.0
pyyaml
httpx>=0.24.0
pydantic>=2.5.3
```

### Language Support

Three-language template system with fallback chain:
1. English (mandatory for all offers)
2. Hindi (optional)
3. Gujarati (optional)