"""Telegram bot entry point and conversation registration."""

import asyncio
import logging
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    ContextTypes,
    Defaults,
    MessageHandler,
    filters,
)

from bot.handlers.body import BODY_HEIGHT, BODY_WEIGHT, body_height, body_measurement_command, body_weight
from bot.handlers.cardio import cardio_command
from bot.handlers.reminder import (
    REMINDER_DELETE_SELECT,
    REMINDER_DAYS,
    REMINDER_EDIT_DAYS,
    REMINDER_EDIT_SELECT,
    REMINDER_EDIT_TIME,
    REMINDER_TIME,
    REST_MINUTES,
    reminder_add_start,
    reminder_command,
    reminder_delete_select,
    reminder_delete_start,
    reminder_days,
    reminder_days_done,
    reminder_day_toggle,
    reminder_edit_day_toggle,
    reminder_edit_days_done,
    reminder_edit_days,
    reminder_edit_select,
    reminder_edit_start,
    reminder_edit_time,
    reminder_list_callback,
    reminder_time,
    rest_timer_command,
    rest_timer_input,
)
from bot.handlers.split import (
    ADD_EXERCISES,
    ADD_NAME,
    ADD_PR,
    DELETE_ACTION,
    DELETE_CONFIRM,
    DELETE_EXERCISE_SELECT,
    DELETE_SELECT,
    EDIT_ACTION,
    EDIT_INPUT,
    EDIT_SELECT,
    add_split_command,
    add_split_exercises,
    add_split_name,
    add_split_pr,
    add_split_start,
    delete_confirm,
    delete_exercise_select,
    delete_split_action,
    delete_split_command,
    delete_split_menu,
    delete_split_select,
    edit_split_action,
    edit_split_command,
    edit_split_input,
    edit_split_menu,
    edit_split_select,
)
from bot.handlers.start import start_command
from bot.handlers.statistics import statistics_command
from bot.handlers.workout import (
    END_SET,
    NEXT_SET,
    PR_INPUT,
    SELECT_SPLIT,
    end_workout_command,
    end_set_input,
    next_exercise_command,
    next_set_input,
    previous_exercise_command,
    pr_input,
    select_workout_split,
    start_workout_command,
    update_pr_command,
)
from bot.services.reminder_service import schedule_all_reminders
from config.settings import BOT_TOKEN, DEFAULT_TIMEZONE

logger = logging.getLogger(__name__)


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    preserved = {
        key: context.user_data[key]
        for key in ("workout_session_id", "workout_pending_sets", "workout_pending_prs")
        if key in context.user_data
    }
    context.user_data.clear()
    context.user_data.update(preserved)
    await update.message.reply_text("Proses dibatalkan.")
    return ConversationHandler.END


async def previous_and_end_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allow /prv while a set or PR input conversation is active."""
    await previous_exercise_command(update, context)
    return ConversationHandler.END


async def end_and_end_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allow /end while a set or PR input conversation is active."""
    return await end_workout_command(update, context)


async def start_and_end_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset the current conversation and show the main menu."""
    await start_command(update, context)
    return ConversationHandler.END


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Command tidak dikenali. Gunakan /start untuk melihat menu.")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors and return a user-friendly message instead of failing silently."""
    logger.exception("Exception while processing update", exc_info=context.error)
    if update and getattr(update, "effective_message", None):
        await update.effective_message.reply_text(
            "Terjadi kesalahan saat memproses permintaan. Silakan coba lagi."
        )


async def post_init(application):
    """Restore recurring reminders after the bot starts."""
    try:
        schedule_all_reminders(application)
    except Exception as error:
        # The bot can still start when MariaDB is temporarily unavailable.
        print(f"Reminder restore dilewati: {error}")


def build_application():
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN belum diatur di file .env")

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .defaults(Defaults(tzinfo=ZoneInfo(DEFAULT_TIMEZONE)))
        .post_init(post_init)
        .build()
    )

    text = filters.TEXT & ~filters.COMMAND
    conversations = [
        ConversationHandler(
            entry_points=[
                CommandHandler("add", add_split_command),
                CallbackQueryHandler(add_split_start, pattern=r"^split:add$"),
                CallbackQueryHandler(edit_split_menu, pattern=r"^split:edit$"),
                CallbackQueryHandler(delete_split_menu, pattern=r"^split:delete$"),
            ],
            states={
                ADD_NAME: [MessageHandler(text, add_split_name)],
                ADD_EXERCISES: [MessageHandler(text, add_split_exercises)],
                ADD_PR: [MessageHandler(text, add_split_pr)],
                EDIT_SELECT: [
                    CallbackQueryHandler(edit_split_select, pattern=r"^split:editselect:\d+$")
                ],
                EDIT_ACTION: [
                    CallbackQueryHandler(edit_split_action, pattern=r"^split:editaction:(name|add|remove|reorder)$")
                ],
                EDIT_INPUT: [MessageHandler(text, edit_split_input)],
                DELETE_SELECT: [
                    CallbackQueryHandler(delete_split_select, pattern=r"^split:deleteselect:\d+$")
                ],
                DELETE_ACTION: [
                    CallbackQueryHandler(delete_split_action, pattern=r"^split:deleteaction:(split|exercise)$")
                ],
                DELETE_EXERCISE_SELECT: [
                    CallbackQueryHandler(delete_exercise_select, pattern=r"^split:deleteexercise:\d+$")
                ],
                DELETE_CONFIRM: [
                    CallbackQueryHandler(
                        delete_confirm,
                        pattern=r"^split:(deleteconfirm|deleteexerciseconfirm)$",
                    )
                ],
            },
            fallbacks=[
                CommandHandler("cancel", cancel_command),
                CommandHandler("start", start_and_end_conversation),
            ],
            allow_reentry=True,
        ),
        ConversationHandler(
            entry_points=[CommandHandler("swo", start_workout_command)],
            states={
                SELECT_SPLIT: [
                    MessageHandler(text, select_workout_split),
                    CallbackQueryHandler(select_workout_split, pattern=r"^split_select:\d+$"),
                ]
            },
            fallbacks=[
                CommandHandler("cancel", cancel_command),
                CommandHandler("start", start_and_end_conversation),
            ],
            allow_reentry=True,
        ),
        ConversationHandler(
            entry_points=[
                CommandHandler("pr", update_pr_command),
                CallbackQueryHandler(update_pr_command, pattern=r"^workout:pr$"),
            ],
            states={
                PR_INPUT: [MessageHandler(text, pr_input)],
                END_SET: [MessageHandler(text, end_set_input)],
            },
            fallbacks=[
                CommandHandler("cancel", cancel_command),
                CommandHandler("prv", previous_and_end_conversation),
                CommandHandler("end", end_and_end_conversation),
                CommandHandler("start", start_and_end_conversation),
            ],
            allow_reentry=True,
        ),
        ConversationHandler(
            entry_points=[
                CommandHandler("rst", rest_timer_command),
                CallbackQueryHandler(rest_timer_command, pattern=r"^workout:rest$"),
            ],
            states={REST_MINUTES: [MessageHandler(text, rest_timer_input)]},
            fallbacks=[
                CommandHandler("cancel", cancel_command),
                CommandHandler("start", start_and_end_conversation),
            ],
            allow_reentry=True,
        ),
        ConversationHandler(
            entry_points=[
                CommandHandler("ntf", reminder_command),
                CallbackQueryHandler(reminder_add_start, pattern=r"^reminder:add$"),
                CallbackQueryHandler(reminder_list_callback, pattern=r"^reminder:list$"),
                CallbackQueryHandler(reminder_edit_start, pattern=r"^reminder:edit$"),
                CallbackQueryHandler(reminder_delete_start, pattern=r"^reminder:delete$"),
            ],
            states={
                REMINDER_DAYS: [
                    MessageHandler(text, reminder_days),
                    CallbackQueryHandler(reminder_day_toggle, pattern=r"^reminder:day:\d+$"),
                    CallbackQueryHandler(reminder_days_done, pattern=r"^reminder:day:done$"),
                ],
                REMINDER_TIME: [MessageHandler(text, reminder_time)],
                REMINDER_EDIT_SELECT: [
                    CallbackQueryHandler(reminder_edit_select, pattern=r"^reminder:editselect:\d+$")
                ],
                REMINDER_EDIT_DAYS: [
                    MessageHandler(text, reminder_edit_days),
                    CallbackQueryHandler(reminder_edit_day_toggle, pattern=r"^reminder:editday:\d+$"),
                    CallbackQueryHandler(
                        reminder_edit_days_done, pattern=r"^reminder:editday:done$"
                    ),
                ],
                REMINDER_EDIT_TIME: [MessageHandler(text, reminder_edit_time)],
                REMINDER_DELETE_SELECT: [
                    CallbackQueryHandler(
                        reminder_delete_select, pattern=r"^reminder:deleteselect:\d+$"
                    )
                ],
            },
            fallbacks=[
                CommandHandler("cancel", cancel_command),
                CommandHandler("start", start_and_end_conversation),
            ],
            allow_reentry=True,
        ),
        ConversationHandler(
            entry_points=[
                CommandHandler("nxt", next_exercise_command),
                CallbackQueryHandler(next_exercise_command, pattern=r"^workout:nxt$"),
            ],
            states={
                NEXT_SET: [MessageHandler(text, next_set_input)],
                END_SET: [MessageHandler(text, end_set_input)],
            },
            fallbacks=[
                CommandHandler("cancel", cancel_command),
                CommandHandler("prv", previous_and_end_conversation),
                CommandHandler("end", end_and_end_conversation),
                CommandHandler("start", start_and_end_conversation),
            ],
            allow_reentry=True,
        ),
        ConversationHandler(
            entry_points=[
                CommandHandler("end", end_workout_command),
                CallbackQueryHandler(end_workout_command, pattern=r"^workout:end$"),
            ],
            states={END_SET: [MessageHandler(text, end_set_input)]},
            fallbacks=[
                CommandHandler("cancel", cancel_command),
                CommandHandler("start", start_and_end_conversation),
            ],
            allow_reentry=True,
        ),
        ConversationHandler(
            entry_points=[CommandHandler("bbbt", body_measurement_command)],
            states={
                BODY_WEIGHT: [MessageHandler(text, body_weight)],
                BODY_HEIGHT: [MessageHandler(text, body_height)],
            },
            fallbacks=[
                CommandHandler("cancel", cancel_command),
                CommandHandler("start", start_and_end_conversation),
            ],
            allow_reentry=True,
        ),
    ]
    for conversation in conversations:
        application.add_handler(conversation)

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", start_command))
    application.add_handler(CallbackQueryHandler(previous_exercise_command, pattern=r"^workout:prv$"))
    application.add_handler(CommandHandler("prv", previous_exercise_command))
    application.add_handler(CommandHandler("cardio", cardio_command))
    application.add_handler(CommandHandler("edt", edit_split_command))
    application.add_handler(CommandHandler("del", delete_split_command))
    application.add_handler(CommandHandler("stat", statistics_command))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    application.add_error_handler(error_handler)
    return application


def main():
    application = build_application()
    print("GymBuddy_Bot sedang berjalan...")
    # Python 3.14 no longer creates a default event loop automatically.
    # python-telegram-bot's run_polling() expects one to be available.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
