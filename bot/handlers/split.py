"""Workout split management commands."""

from telegram import Update
from telegram.ext import ContextTypes


async def add_split_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Wizard penambahan workout split akan diimplementasikan berikutnya.")


async def edit_split_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Fitur edit workout split belum tersedia.")


async def delete_split_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Fitur hapus workout split belum tersedia.")
