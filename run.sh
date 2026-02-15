#!/bin/bash
# FinService-Bot - Quick Start Guide
# This script helps you run the bot with proper setup

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   🤖 FinService-Bot Launcher              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"
    pip install -q python-telegram-bot python-dotenv pyyaml
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
fi

echo ""
echo -e "${BLUE}Checking configuration...${NC}"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo -e "${YELLOW}Create a .env file with:${NC}"
    echo "  TELEGRAM_BOT_TOKEN=your_bot_token_here"
    echo "  ADMIN_IDS=your_user_id_here"
    exit 1
fi

# Check if token is set
if ! grep -q "TELEGRAM_BOT_TOKEN" .env; then
    echo -e "${RED}❌ TELEGRAM_BOT_TOKEN not found in .env!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ .env file configured${NC}"

echo ""
echo -e "${BLUE}Available options:${NC}"
echo "  1) Run startup verification (recommended first)"
echo "  2) Run comprehensive debug test"
echo "  3) Start interactive bot (main.py)"
echo "  4) Start alternative bot (bot.py)"
echo "  5) Start continuous scheduler"
echo "  6) Show configuration"
echo "  7) Exit"
echo ""

read -p "Choose an option (1-7): " choice

case $choice in
    1)
        echo -e "${BLUE}Running startup verification...${NC}"
        echo ""
        python test_startup.py
        ;;
    2)
        echo -e "${BLUE}Running debug test suite...${NC}"
        echo ""
        python test_debug.py
        ;;
    3)
        echo -e "${GREEN}🚀 Starting interactive bot (main.py)${NC}"
        echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
        echo ""
        python main.py
        ;;
    4)
        echo -e "${GREEN}🚀 Starting alternative bot (bot.py)${NC}"
        echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
        echo ""
        python bot.py
        ;;
    5)
        echo -e "${GREEN}🚀 Starting continuous scheduler${NC}"
        echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
        echo ""
        python schedular.py --continuous --interval 1.6
        ;;
    6)
        echo -e "${BLUE}Configuration Status:${NC}"
        echo ""
        python -c "
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv()
print('Token Status:', '✓ SET' if os.environ.get('TELEGRAM_BOT_TOKEN') else '✗ NOT SET')
print('Admin IDs:', os.environ.get('ADMIN_IDS', '✗ NOT SET'))
print('Database:', '✓ EXISTS' if Path('fin_referrals.db').exists() else '✗ WILL CREATE')
print('Config File:', '✓ EXISTS' if Path('services_config.yaml').exists() else '✗ WILL CREATE')
"
        echo ""
        ;;
    7)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid option${NC}"
        exit 1
        ;;
esac
