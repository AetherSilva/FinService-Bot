from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config_schema import ServiceType, config_manager
from templates import OfferData, template_engine
from db_layer import db_manager
from typing import Dict, Any

class AdminCommands:
    def __init__(self, admin_ids: list[int]):
        self.ADMIN_IDS = set(admin_ids)
        self.user_sessions: Dict[int, Dict[str, Any]] = {}

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.ADMIN_IDS

    async def check_user(self, update: Update):
        user = update.effective_user
        if not user: return False
        db_manager.register_user(user.id, user.username or "")
        if db_manager.is_user_blocked(user.id):
            await update.message.reply_text("🚫 You are blocked from using this bot.")
            return False
        return True

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_user(update): return
        user_id = update.effective_user.id
        is_admin = self.is_admin(user_id)
        
        msg = "👋 **Welcome to FinReferrals Bot!**\n\nBrowse financial offers across our channels:\n"
        services = config_manager.list_enabled_services()
        for s in services:
            cfg = config_manager.get_service_config(s)
            msg += f"• {cfg.icon} [{cfg.display_name_en}](https://t.me/{cfg.channel.channel_id[1:]})\n"
        
        if is_admin:
            msg += "\n🔐 **Admin Commands:**\n/add_offer, /setup_channels, /stats, /list_services, /block <id>, /unblock <id>"
        
        await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)

    async def cmd_block(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_admin(update.effective_user.id): return
        if not context.args: return await update.message.reply_text("Usage: /block <user_id>")
        db_manager.set_user_block_status(int(context.args[0]), True)
        await update.message.reply_text(f"✅ User {context.args[0]} blocked.")

    async def cmd_unblock(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_admin(update.effective_user.id): return
        if not context.args: return await update.message.reply_text("Usage: /unblock <user_id>")
        db_manager.set_user_block_status(int(context.args[0]), False)
        await update.message.reply_text(f"✅ User {context.args[0]} unblocked.")

    async def cmd_add_offer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_admin(update.effective_user.id): return
        user_id = update.effective_user.id
        self.user_sessions[user_id] = {"state": "awaiting_service", "data": {}}
        services = config_manager.list_enabled_services()
        keyboard = []
        for i in range(0, len(services), 2):
            row = [InlineKeyboardButton(f"{config_manager.get_service_config(s).icon} {config_manager.get_service_config(s).display_name_en}", callback_data=f"service_{s.value}") for s in services[i:i+2]]
            keyboard.append(row)
        await update.message.reply_text("🎯 Select service type:", reply_markup=InlineKeyboardMarkup(keyboard))

    async def cmd_setup_channels(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_admin(update.effective_user.id): return
        user_id = update.effective_user.id
        self.user_sessions[user_id] = {"state": "awaiting_setup_service", "data": {}}
        services = list(ServiceType)
        keyboard = []
        for i in range(0, len(services), 2):
            row = [InlineKeyboardButton(f"{config_manager.get_service_config(s).icon} {config_manager.get_service_config(s).display_name_en}", callback_data=f"setup_{s.value}") for s in services[i:i+2]]
            keyboard.append(row)
        await update.message.reply_text("Select service to set up channel:", reply_markup=InlineKeyboardMarkup(keyboard))

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if not self.is_admin(query.from_user.id): return
        await query.answer()
        user_id = query.from_user.id
        if user_id not in self.user_sessions: return
        session = self.user_sessions[user_id]
        if query.data.startswith("setup_"):
            session["data"]["service_type"] = query.data.replace("setup_", "")
            session["state"] = "awaiting_channel_setup"
            await query.edit_message_text("Enter new Channel ID (starting with @):")
        elif query.data.startswith("service_"):
            session["data"]["service_type"] = query.data.replace("service_", "")
            session["state"] = "awaiting_provider"
            await query.edit_message_text("Enter provider name:")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in self.user_sessions: return
        session = self.user_sessions[user_id]
        text = update.message.text.strip()
        state = session["state"]
        if state == "awaiting_channel_setup":
            if not text.startswith("@"): return await update.message.reply_text("Must start with @")
            config_manager.update_channel_id(ServiceType(session["data"]["service_type"]), text)
            await update.message.reply_text("✅ Updated.")
            del self.user_sessions[user_id]
        elif state == "awaiting_provider":
            session["data"]["provider"] = text
            session["state"] = "awaiting_title_en"
            await update.message.reply_text("Enter title (English):")
        elif state == "awaiting_title_en":
            session["data"]["title_en"] = text
            session["state"] = "awaiting_link"
            await update.message.reply_text("Enter referral link:")
        elif state == "awaiting_link":
            if not text.startswith("https://"): return await update.message.reply_text("Must start with https://")
            session["data"]["referral_link"] = text
            await self._preview_and_confirm(update, session)

    async def _preview_and_confirm(self, update: Update, session: Dict):
        data = session["data"]
        cfg = config_manager.get_service_config(ServiceType(data["service_type"]))
        offer = OfferData(service_type=data["service_type"], provider=data["provider"], title_en=data["title_en"], referral_link=data["referral_link"], icon=cfg.icon)
        session["offer"] = offer
        session["state"] = "awaiting_confirm"
        keyboard = [[InlineKeyboardButton("✅ Confirm", callback_data="confirm_yes"), InlineKeyboardButton("❌ Cancel", callback_data="confirm_no")]]
        await update.message.reply_text(f"Preview:\n{template_engine.render(offer, cfg)}\nConfirm?", reply_markup=InlineKeyboardMarkup(keyboard))

    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_admin(update.effective_user.id): return
        stats = db_manager.get_stats()
        res = "📊 Stats:\n"
        for s in ServiceType:
            st = stats.get(s.value, {"queued": 0, "posted": 0})
            res += f"{s.value}: Q:{st['queued']} P:{st['posted']}\n"
        await update.message.reply_text(res)

    async def cmd_list_services(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_admin(update.effective_user.id): return
        services = config_manager.list_enabled_services()
        res = "📋 Services:\n"
        for s in services:
            cfg = config_manager.get_service_config(s)
            res += f"{cfg.display_name_en}: {cfg.channel.channel_id}\n"
        await update.message.reply_text(res)

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Browse our financial channels via /start. Admin commands are restricted.")
