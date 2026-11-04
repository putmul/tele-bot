"""Exercise navigation and workout completion commands."""

from telegram import Update
from telegram.ext import ContextTypes


async def next_exercise_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Navigasi ke gerakan berikutnya belum tersedia.")


async def previous_exercise_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Navigasi ke gerakan sebelumnya belum tersedia.")


async def end_workout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Penyelesaian sesi workout belum tersedia.")
