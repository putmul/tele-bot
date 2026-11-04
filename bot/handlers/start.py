"""Start and help commands."""

from telegram import Update
from telegram.ext import ContextTypes

from database.connection import register_user

WELCOME_MESSAGE = """Welcome to GymBuddy_Bot!

Your personal workout assistant.

Available Commands:
/swo - Start Workout
/nxt - Next Exercise
/prv - Previous Exercise
/rst - Rest Timer
/pr - Update Personal Record
/end - End Workout
/add - Add Workout Split
/edt - Edit Workout Split
/del - Delete Workout Split
/ntf - Set Gym Reminder
/stat - Workout Statistics
/cardio - Cardio Tracker
/bbbt - Body Measurement
"""


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id, user.username)
    await update.message.reply_text(WELCOME_MESSAGE)
