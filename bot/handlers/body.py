"""Body measurement command."""

from telegram import Update
from telegram.ext import ContextTypes


async def body_measurement_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Pencatatan body measurement belum tersedia.")
