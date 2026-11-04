"""Rest timer and gym reminder commands."""

from telegram import Update
from telegram.ext import ContextTypes


async def rest_timer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Rest timer akan menggunakan JobQueue pada tahap berikutnya.")


async def reminder_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Pengaturan gym reminder belum tersedia.")
