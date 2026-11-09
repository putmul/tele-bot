"""Workout session, navigation, set logging, and PR commands."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.handlers.start import home_command
from bot.services.pr_service import estimate_one_rep_max
from bot.services.workout_view import format_exercise, workout_keyboard
from database.repository import (
    complete_session_with_pending_sets,
    create_session,
    get_active_session,
    get_current_pr,
    get_split_by_number,
    get_splits,
    update_session_position,
)

SELECT_SPLIT, NEXT_SET, PR_INPUT, END_SET = range(4)


def _parse_weight_reps(value):
    if value.strip().lower() in {"skip", "lewati", "-"}:
        return None
    parts = value.replace(",", ".").split()
    if len(parts) != 2:
        raise ValueError("Format harus: berat reps, contoh: 80 8")
    weight = float(parts[0])
    repetitions = int(parts[1])
    if weight <= 0 or repetitions <= 0:
        raise ValueError("Berat dan reps harus lebih dari 0.")
    return weight, repetitions


async def _answer_callback(update):
    if update.callback_query:
        await update.callback_query.answer()


def _pending_sets(context):
    return context.user_data.setdefault("workout_pending_sets", {})


def _pending_prs(context):
    return context.user_data.setdefault("workout_pending_prs", {})


async def start_workout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _answer_callback(update)
    active = get_active_session(update.effective_user.id)
    if active:
        await update.effective_message.reply_text(
            "Anda masih memiliki sesi aktif. Gunakan /end untuk menyelesaikannya."
        )
        return ConversationHandler.END
    splits = get_splits(update.effective_user.id)
    if not splits:
        await update.effective_message.reply_text("Belum ada split. Buat terlebih dahulu dengan /add.")
        return ConversationHandler.END
    keyboard = [
        [
            InlineKeyboardButton(
                f"{index}. {item['split_name']} ({item['exercise_count']})",
                callback_data=f"split_select:{index}",
            )
        ]
        for index, item in enumerate(splits, start=1)
    ]
    await update.effective_message.reply_text(
        "SELECT WORKOUT\n\nPilih workout split:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return SELECT_SPLIT


async def select_workout_split(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _answer_callback(update)
    if update.callback_query:
        value = update.callback_query.data.split(":", 1)[1]
    else:
        value = update.effective_message.text.strip()
    if not value.isdigit():
        await update.effective_message.reply_text("Pilih nomor split yang valid.")
        return SELECT_SPLIT
    split = get_split_by_number(update.effective_user.id, int(value))
    if not split:
        await update.effective_message.reply_text("Workout split tidak ditemukan.")
        return SELECT_SPLIT
    if split["exercise_count"] == 0:
        await update.effective_message.reply_text("Split ini belum memiliki exercise.")
        return ConversationHandler.END
    session_id = create_session(update.effective_user.id, split["id"])
    if not session_id:
        await update.effective_message.reply_text("Gagal membuat sesi atau masih ada sesi aktif.")
        return ConversationHandler.END
    context.user_data["workout_session_id"] = session_id
    context.user_data["workout_pending_sets"] = {}
    context.user_data["workout_pending_prs"] = {}
    session = get_active_session(update.effective_user.id)
    await update.effective_message.reply_text(
        format_exercise(update.effective_user.id, session),
        reply_markup=workout_keyboard(session),
    )
    return ConversationHandler.END


async def _advance_to_next(update, session):
    update_session_position(
        update.effective_user.id,
        session["id"],
        session["current_exercise_order"] + 1,
    )
    next_session = get_active_session(update.effective_user.id)
    await update.effective_message.reply_text(
        format_exercise(update.effective_user.id, next_session),
        reply_markup=workout_keyboard(next_session),
    )


async def next_exercise_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log the current exercise set before moving to the next exercise."""
    await _answer_callback(update)
    session = get_active_session(update.effective_user.id)
    if not session:
        await update.effective_message.reply_text("Tidak ada sesi workout aktif. Gunakan /swo.")
        return ConversationHandler.END
    if session["current_exercise_order"] >= len(session["exercises"]):
        await update.effective_message.reply_text("Anda sudah berada di exercise terakhir.")
        return ConversationHandler.END
    exercise = session["exercises"][session["current_exercise_order"] - 1]
    context.user_data["next_session_id"] = session["id"]
    context.user_data["next_exercise_id"] = exercise["id"]
    if context.args:
        try:
            value = _parse_weight_reps(" ".join(context.args))
        except ValueError as error:
            await update.effective_message.reply_text(str(error))
            return NEXT_SET
        if value:
            weight, repetitions = value
            _pending_sets(context)[exercise["id"]] = {
                "weight": weight,
                "repetitions": repetitions,
            }
        await _advance_to_next(update, session)
        return ConversationHandler.END
    await update.effective_message.reply_text(
        f"{exercise['exercise_name']}\nMasukkan berat dan reps untuk sesi ini "
        "(contoh: 80 8), atau ketik skip:"
    )
    return NEXT_SET


async def next_set_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        value = _parse_weight_reps(update.effective_message.text)
    except ValueError as error:
        await update.effective_message.reply_text(str(error))
        return NEXT_SET
    if value:
        weight, repetitions = value
        _pending_sets(context)[context.user_data["next_exercise_id"]] = {
            "weight": weight,
            "repetitions": repetitions,
        }
    session = get_active_session(update.effective_user.id)
    if session and session["current_exercise_order"] < len(session["exercises"]):
        await _advance_to_next(update, session)
    return ConversationHandler.END


async def previous_exercise_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _answer_callback(update)
    session = get_active_session(update.effective_user.id)
    if not session:
        await update.effective_message.reply_text("Tidak ada sesi workout aktif. Gunakan /swo.")
        return
    if session["current_exercise_order"] <= 1:
        await update.effective_message.reply_text("Anda sudah berada di exercise pertama.")
        return
    update_session_position(
        update.effective_user.id,
        session["id"],
        session["current_exercise_order"] - 1,
    )
    session = get_active_session(update.effective_user.id)
    await update.effective_message.reply_text(
        format_exercise(update.effective_user.id, session),
        reply_markup=workout_keyboard(session),
    )


def _save_pr(telegram_id, context, weight, repetitions):
    exercise_id = context.user_data["pr_exercise_id"]
    current = get_current_pr(telegram_id, exercise_id)
    estimated = estimate_one_rep_max(weight, repetitions)
    is_new = not current or estimated > float(current["estimated_1rm"])
    _pending_sets(context)[exercise_id] = {
        "weight": weight,
        "repetitions": repetitions,
    }
    _pending_prs(context)[exercise_id] = {
        "weight": weight,
        "repetitions": repetitions,
        "estimated_1rm": estimated,
    }
    return is_new, estimated


async def update_pr_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _answer_callback(update)
    session = get_active_session(update.effective_user.id)
    if not session:
        await update.effective_message.reply_text("/pr hanya dapat digunakan saat workout aktif.")
        return ConversationHandler.END
    exercise = session["exercises"][session["current_exercise_order"] - 1]
    context.user_data["pr_session_id"] = session["id"]
    context.user_data["pr_exercise_id"] = exercise["id"]
    if context.args:
        return await _process_pr_input(update, context, " ".join(context.args))
    await update.effective_message.reply_text(
        f"{exercise['exercise_name']}\nMasukkan berat dan reps sekaligus "
        "(contoh: 100 5):"
    )
    return PR_INPUT


async def _process_pr_input(update, context, value):
    try:
        parsed = _parse_weight_reps(value)
        if not parsed:
            raise ValueError("PR tidak boleh skip.")
    except ValueError as error:
        await update.effective_message.reply_text(str(error))
        return PR_INPUT
    weight, repetitions = parsed
    try:
        is_new, estimated = _save_pr(update.effective_user.id, context, weight, repetitions)
    except Exception as error:
        await update.effective_message.reply_text(f"Gagal menyimpan PR: {error}")
        return ConversationHandler.END
    label = "PR diperbarui!" if is_new else "Data tersimpan, tetapi belum melewati PR sebelumnya."
    await update.effective_message.reply_text(
        f"{label}\n\n{weight:g} kg × {repetitions} reps\n"
        f"Estimasi 1RM: {estimate_one_rep_max(weight, repetitions):.2f} kg\n"
        "Data akan disimpan saat workout selesai."
    )
    session = get_active_session(update.effective_user.id)
    if session and session["current_exercise_order"] < len(session["exercises"]):
        await _advance_to_next(update, session)
    elif session:
        await update.effective_message.reply_text(
            format_exercise(update.effective_user.id, session),
            reply_markup=workout_keyboard(session),
        )
    return ConversationHandler.END


async def pr_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _process_pr_input(update, context, update.effective_message.text)


async def _finish_workout(update: Update, context: ContextTypes.DEFAULT_TYPE, session):
    result = complete_session_with_pending_sets(
        update.effective_user.id,
        session["id"],
        context.user_data.get("workout_pending_sets", {}),
        context.user_data.get("workout_pending_prs", {}),
    )
    if not result:
        await update.effective_message.reply_text("Sesi workout tidak dapat diselesaikan.")
        return ConversationHandler.END
    duration = result["duration_seconds"]
    hours, remainder = divmod(duration, 3600)
    minutes = remainder // 60
    for job in context.job_queue.get_jobs_by_name(f"rest:{update.effective_chat.id}"):
        job.schedule_removal()
    context.user_data.pop("workout_session_id", None)
    context.user_data.pop("workout_pending_sets", None)
    context.user_data.pop("workout_pending_prs", None)
    await update.effective_message.reply_text(
        f"WORKOUT SELESAI!\n\nSplit: {session['split_name']}\n"
        f"Durasi: {hours:02d}j {minutes:02d}m\n"
        f"Gerakan: {len(session['exercises'])}\n\nWorkout berhasil disimpan."
    )
    await home_command(update, context)
    return ConversationHandler.END


async def end_workout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _answer_callback(update)
    session = get_active_session(update.effective_user.id)
    if not session:
        await update.effective_message.reply_text("Tidak ada sesi workout aktif.")
        return ConversationHandler.END
    current_exercise = session["exercises"][session["current_exercise_order"] - 1]
    pending = _pending_sets(context)
    if (
        session["current_exercise_order"] == len(session["exercises"])
        and current_exercise["id"] not in pending
    ):
        await update.effective_message.reply_text(
            f"Gerakan terakhir: {current_exercise['exercise_name']}\n"
            "Masukkan beban dan reps (contoh: 80 8)."
        )
        return END_SET
    return await _finish_workout(update, context, session)


async def end_set_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        value = _parse_weight_reps(update.effective_message.text)
    except ValueError as error:
        await update.effective_message.reply_text(str(error))
        return END_SET
    session = get_active_session(update.effective_user.id)
    if not session:
        await update.effective_message.reply_text("Tidak ada sesi workout aktif.")
        return ConversationHandler.END
    if value:
        exercise = session["exercises"][session["current_exercise_order"] - 1]
        weight, repetitions = value
        _pending_sets(context)[exercise["id"]] = {
            "weight": weight,
            "repetitions": repetitions,
        }
    return await _finish_workout(update, context, session)
