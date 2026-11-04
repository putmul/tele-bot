"""Statistics command."""

from telegram import Update
from telegram.ext import ContextTypes


async def statistics_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Statistik workout belum tersedia.")
