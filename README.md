# 🚀 FinReferrals Bot

A production-ready Telegram automation system for routing financial referral offers to service-specific channels.

## ✨ Features
- **Deterministic Routing**: Maps service types (Credit Cards, Loans, etc.) to specific Telegram channels.
- **Multilingual Support**: Supports English (mandatory), Hindi, and Gujarati (optional).
- **Automated Scheduler**: Posts offers every 1.6 hours across all connected channels.
- **Interactive Admin Interface**: Manage offers and channel settings directly via the bot.
- **Bulk Import**: Support for CSV-based bulk offer ingestion.

## 🛠 Tech Stack
- **Language**: Python 3.11
- **Framework**: `python-telegram-bot` (v20+)
- **Storage**: SQLite for offer queue and history.

## 🚀 Setup & Configuration

### 1. Environment Variables
Set the following secrets in your environment:
- `TELEGRAM_BOT_TOKEN`: Your bot token from @BotFather.
- `ADMIN_IDS`: Comma-separated list of Telegram User IDs authorized to manage the bot (e.g., `12345678,87654321`).

### 2. Deployment
Run the bot and scheduler using the configured workflow:
```bash
python bot.py & python schedular.py --continuous --interval 1.6
```

### 3. Channel Setup
Once the bot is running:
1. Send `/start` to verify admin access.
2. Use `/setup_channels` to interactively set the Telegram Channel ID for each service category.
3. Ensure the bot is added as an administrator to all target channels.

## 📂 Project Structure
- `bot.py`: Main Telegram bot application.
- `schedular.py`: Posting engine with auto-interval support.
- `db_layer.py`: Database management and offer storage.
- `admin_commands.py`: Interactive admin command handlers.
- `config_schema.py`: Service taxonomy and channel configuration.
- `templates.py`: Multilingual template engine.
- `csv_validator.py`: CSV import validation logic.

## 📋 Bot Commands
- `/start`: Open admin panel.
- `/add_offer`: Interactive manual offer creation.
- `/setup_channels`: Configure channel IDs for services.
- `/stats`: View queue statistics.
- `/list_services`: List all service categories and mappings.
- `/template`: Download CSV template for bulk import.
- `/help`: Detailed command guide.
