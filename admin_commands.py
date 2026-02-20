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
        if not user or not update.message: return False
        db_manager.register_user(user.id, user.username or "")
        if db_manager.is_user_blocked(user.id):
            await update.message.reply_text("🚫 You are blocked from using this bot.")
            return False
        return True

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_user(update): return
        if not update.effective_user or not update.message: return
        user_id = update.effective_user.id
        is_admin = self.is_admin(user_id)
        
        msg = "💠 <b>FINANCIAL PROTOCOL ACTIVE</b> 💠\n\nWelcome to <b>FinReferrals Core</b>. Select a sector to view active referral vectors:\n\n"
        services = config_manager.list_enabled_services()
        for s in services:
            cfg = config_manager.get_service_config(s)
            msg += f"┃ {cfg.icon} <a href='https://t.me/{cfg.channel.channel_id[1:]}'>{cfg.display_name_en.upper()}</a>\n"
        
        if is_admin:
            msg += "\n🔐 <b>ADMIN CONSOLE UNLOCKED</b>\n"
            msg += "┣ <code>/add_offer</code> — Inject new vector\n"
            msg += "┣ <code>/setup_channels</code> — Protocol re-route\n"
            msg += "┣ <code>/template</code> — CSV bulk import template\n"
            msg += "┣ <code>/cancel</code> — Abort active session\n"
            msg += "┣ <code>/stats</code> — Network analysis\n"
            msg += "┣ <code>/list_services</code> — Registry list\n"
            msg += "┗ <code>/block</code> | <code>/unblock</code> — Access control"
        
        await update.message.reply_text(msg, parse_mode="HTML", disable_web_page_preview=True)

    async def cmd_template(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not update.message: return
        if not self.is_admin(update.effective_user.id): return
        from csv_validator import CSVValidator
        import io
        validator = CSVValidator()
        template = validator.generate_template_csv()
        bio = io.BytesIO(template.encode('utf-8'))
        bio.name = "referral_template.csv"
        await update.message.reply_document(document=bio, caption="📊 <b>PROTOCOL:</b> Use this CSV template for bulk data injection.", parse_mode="HTML")

    async def cmd_block(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not update.message: return
        if not self.is_admin(update.effective_user.id): return
        if not context.args: return await update.message.reply_text("Usage: /block <user_id>")
        try:
            db_manager.set_user_block_status(int(context.args[0]), True)
            await update.message.reply_text(f"✅ User {context.args[0]} blocked.")
        except (ValueError, IndexError):
            await update.message.reply_text("❌ Invalid User ID.")

    async def cmd_unblock(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not update.message: return
        if not self.is_admin(update.effective_user.id): return
        if not context.args: return await update.message.reply_text("Usage: /unblock <user_id>")
        try:
            db_manager.set_user_block_status(int(context.args[0]), False)
            await update.message.reply_text(f"✅ User {context.args[0]} unblocked.")
        except (ValueError, IndexError):
            await update.message.reply_text("❌ Invalid User ID.")

    async def cmd_add_offer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not update.message: return
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
        if not update.effective_user or not update.message: return
        if not self.is_admin(update.effective_user.id): return
        user_id = update.effective_user.id
        self.user_sessions[user_id] = {"state": "awaiting_setup_service", "data": {}}
        services = list(ServiceType)
        keyboard = []
        for i in range(0, len(services), 2):
            row = [InlineKeyboardButton(f"{config_manager.get_service_config(s).icon} {config_manager.get_service_config(s).display_name_en}", callback_data=f"setup_{s.value}") for s in services[i:i+2]]
            keyboard.append(row)
        await update.message.reply_text("Select service to set up channel:", reply_markup=InlineKeyboardMarkup(keyboard))

    async def _preview_and_confirm(self, update: Update, session: Dict):
        if not update.effective_user or not update.message: return
        data = session["data"]
        try:
            cfg = config_manager.get_service_config(ServiceType(data["service_type"]))
            offer = OfferData(
                service_type=data["service_type"], 
                provider=data["provider"], 
                title_en=data["title_en"], 
                referral_link=data["referral_link"], 
                icon=cfg.icon
            )
            session["offer"] = offer
            session["state"] = "awaiting_confirm"
            keyboard = [
                [
                    InlineKeyboardButton("✅ DEPLOY VECTOR", callback_data="confirm_yes"), 
                    InlineKeyboardButton("❌ ABORT", callback_data="confirm_no")
                ]
            ]
            preview_text = f"📡 <b>VECTOR PREVIEW:</b>\n\n{template_engine.render(offer, cfg)}\n\n<b>INITIATE DEPLOYMENT?</b>"
            await update.message.reply_text(preview_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        except Exception as e:
            await update.message.reply_text(f"❌ Error generating preview: {str(e)}")
            del self.user_sessions[update.effective_user.id]

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if not query or not query.from_user or not self.is_admin(query.from_user.id): return
        await query.answer()
        user_id = query.from_user.id
        if user_id not in self.user_sessions: return
        session = self.user_sessions[user_id]
        
        if query.data and query.data.startswith("setup_"):
            session["data"]["service_type"] = query.data.replace("setup_", "")
            session["state"] = "awaiting_channel_setup"
            await query.edit_message_text("📡 <b>PROTOCOL:</b> Enter new Channel ID (starting with @):", parse_mode="HTML")
        elif query.data and query.data.startswith("service_"):
            session["data"]["service_type"] = query.data.replace("service_", "")
            session["state"] = "awaiting_provider"
            await query.edit_message_text("🏦 <b>PROTOCOL:</b> Enter provider name:", parse_mode="HTML")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not update.message or not update.message.text: return
        user_id = update.effective_user.id
        if user_id not in self.user_sessions: return
        session = self.user_sessions[user_id]
        text = update.message.text.strip()
        state = session["state"]
        
        if state == "awaiting_channel_setup":
            if not text.startswith("@"): return await update.message.reply_text("❌ <b>ERROR:</b> ID must start with @", parse_mode="HTML")
            config_manager.update_channel_id(ServiceType(session["data"]["service_type"]), text)
            await update.message.reply_text("✅ <b>PROTOCOL UPDATED:</b> Channel re-routed.", parse_mode="HTML")
            del self.user_sessions[user_id]
        elif state == "awaiting_provider":
            session["data"]["provider"] = text
            session["state"] = "awaiting_title_en"
            await update.message.reply_text("🎯 <b>PROTOCOL:</b> Enter title (English):", parse_mode="HTML")
        elif state == "awaiting_title_en":
            session["data"]["title_en"] = text
            session["state"] = "awaiting_link"
            await update.message.reply_text("🔗 <b>PROTOCOL:</b> Enter referral link:", parse_mode="HTML")
        elif state == "awaiting_link":
            if not text.startswith("https://"): return await update.message.reply_text("❌ <b>ERROR:</b> Link must start with https://", parse_mode="HTML")
            session["data"]["referral_link"] = text
            await self._preview_and_confirm(update, session)

    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not update.message: return
        if not self.is_admin(update.effective_user.id): return
        stats = db_manager.get_stats()
        res = "📊 <b>NETWORK TRAFFIC ANALYSIS</b>\n\n"
        for s in ServiceType:
            st = stats.get(s.value, {"queued": 0, "posted": 0, "failed": 0})
            res += f"<b>{s.value.upper()}:</b>\n"
            res += f"┣ 📥 QUEUED: <code>{st['queued']}</code>\n"
            res += f"┣ 📤 POSTED: <code>{st['posted']}</code>\n"
            res += f"┗ ⚠️ FAILED: <code>{st['failed']}</code>\n\n"
        await update.message.reply_text(res, parse_mode="HTML")

    async def cmd_list_services(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not update.message: return
        if not self.is_admin(update.effective_user.id): return
        services = config_manager.list_enabled_services()
        res = "📋 <b>ACTIVE SECTOR REGISTRY</b>\n\n"
        for s in services:
            cfg = config_manager.get_service_config(s)
            res += f"<b>{cfg.display_name_en.upper()}:</b>\n"
            res += f"┗ 🛰️ <code>{cfg.channel.channel_id}</code>\n\n"
        await update.message.reply_text(res, parse_mode="HTML")

    async def cmd_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not update.message: return
        user_id = update.effective_user.id
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
            await update.message.reply_text("🛑 <b>PROTOCOL ABORTED:</b> Session cleared.", parse_mode="HTML")
        else:
            await update.message.reply_text("❌ <b>ERROR:</b> No active protocol session.", parse_mode="HTML")

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not update.message: return
        help_text = "🆘 <b>FINANCIAL PROTOCOL ASSISTANCE</b>\n\n"
        help_text += "• /start — Initialize portal\n"
        if self.is_admin(update.effective_user.id):
            help_text += "\n🔐 <b>ADMIN COMMANDS:</b>\n"
            help_text += "• /add_offer — Inject new vector\n"
            help_text += "• /setup_channels — Protocol re-route\n"
            help_text += "• /template — Get CSV bulk import template\n"
            help_text += "• /cancel — Abort active session\n"
            help_text += "• /stats — Network analysis\n"
            help_text += "• /list_services — Registry list\n"
            help_text += "• /block <code>ID</code> — Restrict access\n"
            help_text += "• /unblock <code>ID</code> — Restore access\n"
            help_text += "\n💡 <b>PRO TIP:</b> Upload a CSV file directly for bulk import."
        else:
            help_text += "Browse our financial sectors via /start to find active referral links."
        await update.message.reply_text(help_text, parse_mode="HTML")
