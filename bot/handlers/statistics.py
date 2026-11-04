"""Statistics command."""

from telegram import Update
from telegram.ext import ContextTypes

from database.repository import get_statistics


async def statistics_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        stats = get_statistics(update.effective_user.id)
    except Exception as error:
        await update.message.reply_text(f"Gagal mengambil statistik: {error}")
        return
    hours = float(stats["total_duration"]) / 3600
    message = (
        "STATISTIK GYM\n\n"
        f"Total Gerakan: {stats['total_workouts']}\n"
        f"Total Jam : {hours:.2f} hours\n"
        f"Total Set: {stats['total_sets']}\n\n"
        "Personal Records:\n"
    )
    if stats["prs"]:
        message += "\n".join(
            f"{row['exercise_name']}: {float(row['weight_kg']):g} kg × "
            f"{row['repetitions']} reps"
            for row in stats["prs"]
        )
    else:
        message += "Belum ada PR."
    await update.message.reply_text(message)
