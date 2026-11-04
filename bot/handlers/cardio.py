"""Cardio tracker command."""

from telegram import Update
from telegram.ext import ContextTypes


async def cardio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Pencatatan cardio belum tersedia.")
