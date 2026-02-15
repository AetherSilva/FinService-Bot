#!/usr/bin/env python3
"""
Test script to verify bot startup configuration without running polling.
This verifies that all environment variables and imports are correct.
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✓ Loaded .env from {env_path}")
else:
    print(f"❌ .env file not found at {env_path}")
    sys.exit(1)

print("\n" + "="*60)
print("📋 FinService-Bot Startup Verification")
print("="*60 + "\n")

# Test 1: Check environment variables
print("1️⃣  Checking environment variables...")
token = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN")
if token:
    print(f"   ✓ TELEGRAM_BOT_TOKEN: {token[:20]}...")
else:
    print(f"   ❌ TELEGRAM_BOT_TOKEN not found")
    sys.exit(1)

admin_ids_raw = os.environ.get("ADMIN_IDS", "")
if admin_ids_raw:
    admin_ids = [int(x.strip()) for x in admin_ids_raw.split(",") if x.strip()]
    print(f"   ✓ ADMIN_IDS: {admin_ids}")
else:
    print(f"   ⚠ ADMIN_IDS not configured")

# Test 2: Import all required modules
print("\n2️⃣  Importing required modules...")
try:
    from telegram.ext import Application
    print("   ✓ telegram.ext.Application")
    
    from config_schema import config_manager, ServiceType
    print("   ✓ config_schema module")
    
    from db_layer import db_manager
    print("   ✓ db_layer module")
    
    from templates import template_engine
    print("   ✓ templates module")
    
    from admin_commands import AdminCommands
    print("   ✓ admin_commands module")
    
    from csv_validator import CSVValidator
    print("   ✓ csv_validator module")
    
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

# Test 3: Verify database initialization
print("\n3️⃣  Verifying database...")
try:
    stats = db_manager.get_stats()
    print(f"   ✓ Database initialized with {len(stats)} service types")
    queued_count = sum(s.get('queued', 0) for s in stats.values())
    print(f"   ✓ Queued offers: {queued_count}")
except Exception as e:
    print(f"   ❌ Database error: {e}")
    sys.exit(1)

# Test 4: Verify configuration
print("\n4️⃣  Verifying service configuration...")
try:
    services = config_manager.list_enabled_services()
    print(f"   ✓ Enabled services: {len(services)}")
    for service in services[:3]:
        cfg = config_manager.get_service_config(service)
        print(f"     - {cfg.display_name_en} → {cfg.channel.channel_id}")
except Exception as e:
    print(f"   ❌ Configuration error: {e}")
    sys.exit(1)

# Test 5: Verify bot can be created
print("\n5️⃣  Creating bot application...")
try:
    from telegram.constants import ParseMode
    from telegram import LinkPreviewOptions
    from telegram.ext import Defaults
    
    defaults = Defaults(
        parse_mode=ParseMode.HTML,
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )
    app = Application.builder().token(token).defaults(defaults).build()
    print("   ✓ Bot application created successfully")
except Exception as e:
    print(f"   ❌ Bot creation failed: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("✅ All startup checks passed!")
print("="*60)
print("\nYou can now run:")
print("  - python main.py          (Interactive bot mode)")
print("  - python bot.py           (Alternative bot mode)")
print("  - python schedular.py --continuous  (Scheduled posting)")
print("\nNote: Telegram polling will start once you run one of the above commands.")
print("Make sure the bot is added to all channels before running.")
