import os
import sys
import logging
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✓ Loaded .env from {env_path}")
else:
    print(f"⚠ .env file not found at {env_path}")

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from admin_commands import AdminCommands
from csv_validator import CSVValidator
from db_layer import db_manager
from templates import template_engine

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Global admin_commands instance for handlers
admin_commands = None

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_commands or not update.effective_user or not update.message or not update.message.document: return
    if not admin_commands.is_admin(update.effective_user.id): return
    doc = update.message.document
    if not doc.file_name or not doc.file_name.endswith('.csv'): 
        return await update.message.reply_text("Upload CSV")
    file = await doc.get_file()
    content = (await file.download_as_bytearray()).decode('utf-8')
    res = CSVValidator().validate_csv_content(content)
    if not res.valid: return await update.message.reply_text("Invalid CSV")
    for o in res.offers: db_manager.insert_offer(o)
    await update.message.reply_text("✅ Imported")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not admin_commands or not query or not query.data or not query.from_user: return
    if query.data.startswith("confirm_"):
        if not admin_commands.is_admin(query.from_user.id): return
        uid = query.from_user.id
        if uid not in admin_commands.user_sessions: return await query.answer("Expired")
        if query.data == "confirm_yes":
            db_manager.insert_offer(admin_commands.user_sessions[uid]["offer"])
            await query.edit_message_text("✅ Queued")
        else: await query.edit_message_text("❌ Cancelled")
        del admin_commands.user_sessions[uid]
    else: await admin_commands.handle_callback(update, context)

def main():
    global admin_commands
    BOT_TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
    ADMIN_IDS_RAW = os.environ.get("ADMIN_IDS", "")
    
    if not BOT_TOKEN:
        logger.error("❌ Missing TELEGRAM_BOT_TOKEN/BOT_TOKEN environment variable")
        logger.error("   Please ensure TELEGRAM_BOT_TOKEN is set in your .env file or environment.")
        logger.error(f"   Checked locations: .env file at {Path(__file__).parent / '.env'}")
        sys.exit(1)
    
    logger.info("✓ TELEGRAM_BOT_TOKEN loaded successfully")
    
    try:
        ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_RAW.split(",") if x.strip()]
    except ValueError:
        logger.error(f"❌ Invalid ADMIN_IDS format: {ADMIN_IDS_RAW}")
        logger.error("   Expected: comma-separated list of user IDs (e.g., '123456,789012')")
        ADMIN_IDS = []
    
    if ADMIN_IDS:
        logger.info(f"✓ Admin IDs configured: {ADMIN_IDS}")
    else:
        logger.warning("⚠ No admin IDs configured. Set ADMIN_IDS in .env to enable admin features.")
    
    try:
        admin_commands = AdminCommands(ADMIN_IDS)
        app = Application.builder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", admin_commands.cmd_start))
        app.add_handler(CommandHandler("setup_channels", admin_commands.cmd_setup_channels))
        app.add_handler(CommandHandler("add_offer", admin_commands.cmd_add_offer))
        app.add_handler(CommandHandler("stats", admin_commands.cmd_stats))
        app.add_handler(CommandHandler("list_services", admin_commands.cmd_list_services))
        app.add_handler(CommandHandler("block", admin_commands.cmd_block))
        app.add_handler(CommandHandler("unblock", admin_commands.cmd_unblock))
        app.add_handler(CommandHandler("help", admin_commands.cmd_help))
        app.add_handler(CallbackQueryHandler(callback_handler))
        app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_commands.handle_message))
        
        logger.info("=" * 50)
        logger.info("🚀 FinService-Bot is starting...")
        logger.info("=" * 50)
        app.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__": main()
