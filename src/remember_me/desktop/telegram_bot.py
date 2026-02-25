"""
Telegram Bot Adapter — Refactored from Zyron's monolithic handler.
===================================================================
Routes all messages through Kernel.run_cycle() instead of keyword matching.

SECURITY CHANGES:
- Authentication via user.id (immutable) not user.username (spoofable)
- Authorized user IDs configured via environment variable
"""

import asyncio
import logging
import os
from typing import Optional, Set

logger = logging.getLogger("TELEGRAM")

# Lazy import
_telegram_available = False
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        CallbackQueryHandler,
        filters,
        ContextTypes,
    )
    _telegram_available = True
except ImportError:
    logger.warning("python-telegram-bot not installed.")


def _get_authorized_ids() -> Set[int]:
    """
    Load authorized Telegram user IDs from environment.
    REMEMBER_ME_TELEGRAM_USER_IDS="123456789,987654321"
    """
    raw = os.environ.get("REMEMBER_ME_TELEGRAM_USER_IDS", "")
    ids = set()
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            ids.add(int(part))
    return ids


class TelegramAdapter:
    """
    Connects the Remember-Me Kernel to a Telegram bot.

    Usage:
        from remember_me.kernel import Kernel
        kernel = Kernel()
        bot = TelegramAdapter(kernel, token="BOT_TOKEN")
        bot.run()
    """

    def __init__(self, kernel, token: Optional[str] = None):
        if not _telegram_available:
            raise ImportError("python-telegram-bot is required: pip install python-telegram-bot")

        self.kernel = kernel
        self.token = token or os.environ.get("REMEMBER_ME_TELEGRAM_TOKEN", "")
        if not self.token:
            raise ValueError("Telegram token required (env: REMEMBER_ME_TELEGRAM_TOKEN)")

        self.authorized_ids = _get_authorized_ids()
        if not self.authorized_ids:
            logger.warning("No authorized user IDs configured (env: REMEMBER_ME_TELEGRAM_USER_IDS). Bot will reject all messages.")

    def _is_authorized(self, user_id: int) -> bool:
        """Check authorization via immutable user ID."""
        if not self.authorized_ids:
            return False
        return user_id in self.authorized_ids

    # ─── HANDLERS ────────────────────────────────────────────────

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update.effective_user.id):
            await update.message.reply_text("⛔ Unauthorized.")
            return
        await update.message.reply_text(
            "🧠 **Remember-Me AI** is online.\n"
            "Send any message and I'll process it through the Sovereign Agent.\n\n"
            "Commands:\n"
            "/status — System health\n"
            "/screenshot — Capture screen\n"
            "/battery — Battery info\n"
            "/storage — Disk usage\n"
            "/clipboard — Recent clipboard\n"
            "/panic — Emergency lock",
            parse_mode="Markdown",
        )

    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update.effective_user.id):
            return
        result = self.kernel.execute_desktop_tool("get_system_health")
        await update.message.reply_text(str(result))

    async def _cmd_screenshot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update.effective_user.id):
            return
        await update.message.reply_text("📸 Taking screenshot...")
        result = self.kernel.execute_desktop_tool("take_screenshot")
        if result and os.path.exists(result):
            with open(result, "rb") as photo:
                await update.message.reply_photo(photo)
        else:
            await update.message.reply_text("❌ Screenshot failed.")

    async def _cmd_battery(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update.effective_user.id):
            return
        result = self.kernel.execute_desktop_tool("get_battery")
        await update.message.reply_text(str(result))

    async def _cmd_storage(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update.effective_user.id):
            return
        result = self.kernel.execute_desktop_tool("check_storage")
        await update.message.reply_text(str(result))

    async def _cmd_clipboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update.effective_user.id):
            return
        if self.kernel._clipboard:
            history = self.kernel._clipboard.get_history(limit=5)
            if history:
                text = "\n\n".join(
                    f"📋 {entry['timestamp'][:16]}\n{entry['text'][:200]}"
                    for entry in reversed(history)
                )
                await update.message.reply_text(text)
            else:
                await update.message.reply_text("Clipboard history is empty.")
        else:
            await update.message.reply_text("Clipboard monitor not active.")

    async def _cmd_panic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update.effective_user.id):
            return
        await update.message.reply_text("🚨 PANIC MODE — Locking system...")
        result = self.kernel.execute_desktop_tool("system_panic")
        await update.message.reply_text(str(result))

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Route all free-text messages through Kernel.run_cycle()."""
        if not self._is_authorized(update.effective_user.id):
            await update.message.reply_text("⛔ Unauthorized.")
            return

        user_text = update.message.text
        if not user_text:
            return

        try:
            # Run through the full Sovereign Agent pipeline
            response = self.kernel.run_cycle(user_text)

            # Handle long responses (Telegram 4096 char limit)
            if len(response) > 4000:
                for i in range(0, len(response), 4000):
                    await update.message.reply_text(response[i:i+4000])
            else:
                await update.message.reply_text(response)

        except Exception as e:
            logger.error(f"Message handling error: {e}")
            await update.message.reply_text(f"❌ Error: {e}")

    # ─── RUN ─────────────────────────────────────────────────────

    def run(self):
        """Start the Telegram bot (blocking)."""
        app = Application.builder().token(self.token).build()

        # Register command handlers
        app.add_handler(CommandHandler("start", self._cmd_start))
        app.add_handler(CommandHandler("status", self._cmd_status))
        app.add_handler(CommandHandler("screenshot", self._cmd_screenshot))
        app.add_handler(CommandHandler("battery", self._cmd_battery))
        app.add_handler(CommandHandler("storage", self._cmd_storage))
        app.add_handler(CommandHandler("clipboard", self._cmd_clipboard))
        app.add_handler(CommandHandler("panic", self._cmd_panic))

        # Free-text → Kernel
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))

        logger.info("Telegram bot starting...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
