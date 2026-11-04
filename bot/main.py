"""Telegram bot entry point."""

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from bot.handlers.body import body_measurement_command
from bot.handlers.cardio import cardio_command
from bot.handlers.exercise import end_workout_command, next_exercise_command, previous_exercise_command
from bot.handlers.reminder import reminder_command, rest_timer_command
from bot.handlers.split import add_split_command, delete_split_command, edit_split_command
from bot.handlers.start import start_command
from bot.handlers.statistics import statistics_command
from bot.handlers.workout import start_workout_command, update_pr_command
from config.settings import BOT_TOKEN


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Command tidak dikenali. Gunakan /start untuk melihat menu.")


def build_application():
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN belum diatur di file .env")

    application = Application.builder().token(BOT_TOKEN).build()
    handlers = {
        "start": start_command,
        "swo": start_workout_command,
        "nxt": next_exercise_command,
        "prv": previous_exercise_command,
        "rst": rest_timer_command,
        "pr": update_pr_command,
        "end": end_workout_command,
        "add": add_split_command,
        "edt": edit_split_command,
        "del": delete_split_command,
        "ntf": reminder_command,
        "stat": statistics_command,
        "cardio": cardio_command,
        "bbbt": body_measurement_command,
    }
    for command, callback in handlers.items():
        application.add_handler(CommandHandler(command, callback))
    application.add_handler(CommandHandler("help", start_command))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    return application


def main():
    application = build_application()
    print("GymBuddy_Bot sedang berjalan...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
