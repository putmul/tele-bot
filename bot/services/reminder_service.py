"""Telegram JobQueue helpers for rest and gym reminders."""

from datetime import time, timedelta

from bot.services.workout_view import format_exercise, workout_keyboard
from database.repository import get_active_reminders, get_active_session


async def rest_complete_callback(context):
    chat_id = context.job.chat_id
    await context.bot.send_message(
        chat_id=chat_id,
        text="ISTIRAHAT SELESAI!\n\nWaktunya melanjutkan latihan.",
    )
    session = get_active_session(chat_id)
    if session:
        await context.bot.send_message(
            chat_id=chat_id,
            text=format_exercise(chat_id, session),
            reply_markup=workout_keyboard(session),
        )


def schedule_rest_timer(context, chat_id, minutes):
    name = f"rest:{chat_id}"
    for job in context.job_queue.get_jobs_by_name(name):
        job.schedule_removal()
    context.job_queue.run_once(
        rest_complete_callback,
        when=minutes * 60,
        chat_id=chat_id,
        name=name,
    )


async def gym_reminder_callback(context):
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text="GYM REMINDER\n\nWaktunya latihan sesuai jadwal Anda!",
    )


def schedule_user_reminders(application, telegram_id):
    """Schedule all active reminders for one user.

    The configured application timezone is used as the default timezone for
    now. The users table already has a timezone field so per-user timezone
    support can be added without changing the reminder data model.
    """
    reminders = get_active_reminders(telegram_id)
    user_id = reminders[0]["user_id"] if reminders else telegram_id
    job_queue = application.job_queue
    for job in job_queue.get_jobs_by_name(f"reminder-user:{user_id}"):
        job.schedule_removal()
    for reminder in reminders:
        reminder_time = reminder["reminder_time"]
        # MariaDB TIME values can be returned by mysql-connector as either
        # datetime.time or datetime.timedelta, depending on the connector
        # mode and the column value.
        if isinstance(reminder_time, timedelta):
            total_seconds = int(reminder_time.total_seconds())
            reminder_time = time(
                hour=(total_seconds // 3600) % 24,
                minute=(total_seconds % 3600) // 60,
                second=total_seconds % 60,
            )
        elif not isinstance(reminder_time, time):
            reminder_time = time(
                hour=reminder_time.hour,
                minute=reminder_time.minute,
                second=getattr(reminder_time, "second", 0),
            )
        job_queue.run_daily(
            gym_reminder_callback,
            time=reminder_time,
            days=(reminder["day_of_week"],),
            chat_id=telegram_id,
            name=f"reminder-user:{user_id}",
        )


def schedule_all_reminders(application):
    """Restore active reminders after bot startup."""
    for reminder in get_active_reminders():
        schedule_user_reminders(application, reminder["telegram_id"])
