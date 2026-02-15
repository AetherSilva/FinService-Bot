import os
import sys
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✓ Loaded .env from {env_path}")
else:
    print(f"⚠ .env file not found at {env_path}")

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    Defaults,
)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions
from telegram.constants import ParseMode

# --- Configuration & Logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("FinServiceBot")

@dataclass
class Offer:
    id: str
    name: str
    bonus: str
    link: str
    description: str
    terms: Optional[str] = None

@dataclass
class Category:
    id: str
    name: str
    emoji: str
    offers: List[Offer]

# --- Data Layer (Simulating advanced logic/structure) ---
class ReferralData:
    def __init__(self):
        self.categories: Dict[str, Category] = {
            "credit_cards": Category(
                id="credit_cards",
                name="Credit Cards",
                emoji="💳",
                offers=[
                    Offer("cc_prem", "Premium Rewards Card", "$200 signup bonus", "https://example.com/premium-card", "High cashback on dining and travel."),
                    Offer("cc_cash", "Cashback Plus Card", "5% cashback first 3 months", "https://example.com/cashback-card", "No annual fee and flexible rewards."),
                ]
            ),
            "banking": Category(
                id="banking",
                name="Banking",
                emoji="🏦",
                offers=[
                    Offer("bnk_sav", "High-Yield Savings", "$100 welcome bonus", "https://example.com/savings", "4.50% APY with no monthly maintenance fees."),
                    Offer("bnk_chk", "Premium Checking", "No fees + $50 bonus", "https://example.com/checking", "Free ATM withdrawals worldwide."),
                ]
            ),
            "investing": Category(
                id="investing",
                name="Investing",
                emoji="📈",
                offers=[
                    Offer("inv_stk", "Stock Trading App", "Free stock up to $500", "https://example.com/stocks", "Trade stocks, ETFs, and options commission-free."),
                    Offer("inv_cry", "Crypto Exchange", "$25 in Bitcoin", "https://example.com/crypto", "Secure platform for buying and selling digital assets."),
                ]
            )
        }

    def get_all_categories(self) -> List[Category]:
        return list(self.categories.values())

    def get_category(self, cat_id: str) -> Optional[Category]:
        return self.categories.get(cat_id)

    def search_offers(self, query: str) -> List[Offer]:
        results = []
        for cat in self.categories.values():
            for offer in cat.offers:
                if query.lower() in offer.name.lower() or query.lower() in offer.description.lower():
                    results.append(offer)
        return results

# --- Bot Logic ---
class FinServiceBot:
    def __init__(self, data_provider: ReferralData):
        self.data = data_provider

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command with branding and main menu."""
        if not update.effective_user or not update.message: return
        user = update.effective_user
        welcome_text = (
            f"<b>Welcome to FinServiceBot, {user.first_name}!</b> 🚀\n\n"
            "Your premium portal for the best financial referral offers. "
            "Maximize your gains with exclusive bonuses in banking, credit, and investing.\n\n"
            "<i>Select a category below to explore:</i>"
        )
        
        keyboard = []
        categories = self.data.get_all_categories()
        # Build grid layout
        for i in range(0, len(categories), 2):
            row = [
                InlineKeyboardButton(f"{categories[i].emoji} {categories[i].name}", callback_data=f"cat_{categories[i].id}")
            ]
            if i + 1 < len(categories):
                row.append(InlineKeyboardButton(f"{categories[i+1].emoji} {categories[i+1].name}", callback_data=f"cat_{categories[i+1].id}"))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔍 Search Offers", callback_data="menu_search")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Centralized callback query handler."""
        query = update.callback_query
        if not query or not query.data: return
        await query.answer()
        
        data = query.data
        
        if data.startswith("cat_"):
            cat_id = data.replace("cat_", "")
            await self._show_category(query, cat_id)
        elif data == "menu_main":
            await self._show_main_menu(query)
        elif data == "menu_search":
            await query.edit_message_text("Send me a keyword (e.g., 'bonus' or 'crypto') to search for offers.")

    async def _show_category(self, query, cat_id: str):
        category = self.data.get_category(cat_id)
        if not category:
            await query.edit_message_text("Category not found.")
            return

        text = f"<b>{category.emoji} {category.name} Offers</b>\n\n"
        keyboard = []
        for offer in category.offers:
            text += f"• <b>{offer.name}</b>\n   🎁 <i>{offer.bonus}</i>\n   📝 {offer.description}\n\n"
            keyboard.append([InlineKeyboardButton(f"Claim {offer.name}", url=offer.link)])
        
        keyboard.append([InlineKeyboardButton("« Back to Menu", callback_data="menu_main")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    async def _show_main_menu(self, query):
        categories = self.data.get_all_categories()
        keyboard = []
        for i in range(0, len(categories), 2):
            row = [InlineKeyboardButton(f"{categories[i].emoji} {categories[i].name}", callback_data=f"cat_{categories[i].id}")]
            if i + 1 < len(categories):
                row.append(InlineKeyboardButton(f"{categories[i+1].emoji} {categories[i+1].name}", callback_data=f"cat_{categories[i+1].id}"))
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("🔍 Search Offers", callback_data="menu_search")])
        
        welcome_text = "<b>FinServiceBot Main Menu</b>\n\nSelect a category to view the latest referral bonuses:"
        await query.edit_message_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)

def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN")
    if not token:
        logger.error("❌ TELEGRAM_BOT_TOKEN not found in environment variables or .env file.")
        logger.error("   Please ensure TELEGRAM_BOT_TOKEN is set in your .env file or environment.")
        sys.exit(1)

    logger.info("✓ TELEGRAM_BOT_TOKEN loaded successfully")
    
    admin_ids = os.environ.get("ADMIN_IDS", "")
    if admin_ids:
        logger.info(f"✓ Admin IDs configured: {admin_ids}")
    
    try:
        # Advanced Setup
        defaults = Defaults(parse_mode=ParseMode.HTML, link_preview_options=LinkPreviewOptions(is_disabled=True))
        data_provider = ReferralData()
        bot_logic = FinServiceBot(data_provider)

        application = Application.builder().token(token).defaults(defaults).build()

        # Handlers
        application.add_handler(CommandHandler("start", bot_logic.start))
        application.add_handler(CallbackQueryHandler(bot_logic.handle_callback))
        application.add_error_handler(error_handler)

        logger.info("" * 50)
        logger.info("🚀 FinServiceBot is starting...")
        logger.info("" * 50)
        # In Replit environment, use drop_pending_updates to avoid 409 Conflict with multiple instances
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
