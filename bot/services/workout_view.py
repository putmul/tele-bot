"""Shared workout message and inline keyboard presentation helpers."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from database.repository import get_current_pr, get_last_session_set


def workout_keyboard(session):
    position = session["current_exercise_order"]
    total = len(session["exercises"])
    navigation = []
    if position > 1:
        navigation.append(InlineKeyboardButton("⬅️ Sebelumnya", callback_data="workout:prv"))
    if position < total:
        navigation.append(InlineKeyboardButton("Berikutnya ➡️", callback_data="workout:nxt"))
    rows = [navigation] if navigation else []
    rows.extend(
        [
            [InlineKeyboardButton("📝 Catat PR", callback_data="workout:pr")],
            [
                InlineKeyboardButton("⏱ Rest Timer", callback_data="workout:rest"),
                InlineKeyboardButton("✅ Selesai", callback_data="workout:end"),
            ],
        ]
    )
    return InlineKeyboardMarkup(rows)


def format_exercise(telegram_id, session):
    exercises = session["exercises"]
    position = session["current_exercise_order"]
    exercise = exercises[position - 1]
    current_pr = get_current_pr(telegram_id, exercise["id"])
    last_set = get_last_session_set(telegram_id, exercise["id"])
    pr_text = "Belum ada PR"
    if current_pr:
        pr_text = (
            f"{float(current_pr['weight_kg']):g} kg × {current_pr['repetitions']} reps "
            f"(1RM {float(current_pr['estimated_1rm']):.2f} kg)"
        )
    last_text = "Belum ada sesi sebelumnya"
    if last_set:
        last_text = f"{float(last_set['weight_kg']):g} kg × {last_set['repetitions']} reps"
    return (
        f"WORKOUT SESSION: {session['split_name']}\n\n"
        f"Exercise {position}/{len(exercises)}\n{exercise['exercise_name']}\n\n"
        f"Personal Record:\n{pr_text}\n\n"
        f"Last Session:\n{last_text}\n\n"
        "Gunakan tombol di bawah atau command /nxt, /prv, /pr, /rst, /end."
    )
