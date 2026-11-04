"""Workout session commands."""

from telegram import Update
from telegram.ext import ContextTypes


async def start_workout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Fitur memilih workout split akan diimplementasikan pada tahap berikutnya.")


async def update_pr_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Fitur pencatatan Personal Record akan diimplementasikan pada tahap berikutnya.")
