"""Workout split management commands."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.handlers.start import start_command
from database.repository import (
    add_exercise_to_split,
    create_split,
    delete_split,
    get_split_by_number,
    get_split_exercises,
    get_splits,
    remove_exercise_from_split,
    reorder_exercise,
    rename_split,
)

ADD_NAME, ADD_EXERCISES, ADD_PR, EDIT_SELECT, EDIT_ACTION, EDIT_INPUT, DELETE_SELECT, DELETE_ACTION, DELETE_EXERCISE_SELECT, DELETE_CONFIRM = range(10)


def _split_menu_markup():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("➕ Tambah Split", callback_data="split:add")],
            [InlineKeyboardButton("✏️ Edit Split", callback_data="split:edit")],
            [InlineKeyboardButton("🗑 Hapus Split / Exercise", callback_data="split:delete")],
        ]
    )


def _split_list(splits):
    if not splits:
        return "Belum ada workout split."
    return "\n".join(
        f"{index}. {item['split_name']} ({item['exercise_count']} exercise)"
        for index, item in enumerate(splits, start=1)
    )


def _parse_pr(value):
    if value.strip().lower() in {"skip", "none", "no", "-"}:
        return None
    parts = value.replace(",", ".").split()
    if len(parts) != 2:
        raise ValueError("Format PR: berat repetisi, contoh: 100 5 atau skip")
    weight = float(parts[0])
    repetitions = int(parts[1])
    if weight <= 0 or repetitions <= 0:
        raise ValueError("Berat dan repetisi harus lebih dari 0.")
    return weight, repetitions


async def add_split_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _answer_callback(update)
    await update.effective_message.reply_text(
        "KELOLA WORKOUT SPLIT\n\nPilih tindakan:", reply_markup=_split_menu_markup()
    )
    return ConversationHandler.END


async def _answer_callback(update):
    if update.callback_query:
        await update.callback_query.answer()


async def add_split_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _answer_callback(update)
    preserved = {
        key: context.user_data[key]
        for key in ("workout_session_id", "workout_pending_sets", "workout_pending_prs")
        if key in context.user_data
    }
    context.user_data.clear()
    context.user_data.update(preserved)
    await update.effective_message.reply_text(
        "ADD WORKOUT SPLIT\n\nMasukkan nama workout split:"
    )
    return ADD_NAME


async def edit_split_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _answer_callback(update)
    splits = get_splits(update.effective_user.id)
    if not splits:
        await update.effective_message.reply_text("Belum ada workout split untuk diedit.")
        return ConversationHandler.END
    markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"{index}. {split['split_name']}",
                    callback_data=f"split:editselect:{index}",
                )
            ]
            for index, split in enumerate(splits, start=1)
        ]
    )
    await update.effective_message.reply_text("Pilih split yang ingin diedit:", reply_markup=markup)
    return EDIT_SELECT


async def edit_split_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _answer_callback(update)
    split_number = int(update.callback_query.data.rsplit(":", 1)[1])
    split = get_split_by_number(update.effective_user.id, split_number)
    if not split:
        await update.effective_message.reply_text("Split tidak ditemukan.")
        return ConversationHandler.END
    context.user_data["edit_split_id"] = split["id"]
    context.user_data["edit_split_number"] = split_number
    markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Ubah Nama", callback_data="split:editaction:name")],
            [InlineKeyboardButton("Tambah Exercise", callback_data="split:editaction:add")],
            [InlineKeyboardButton("Hapus Exercise", callback_data="split:editaction:remove")],
            [InlineKeyboardButton("Atur Urutan", callback_data="split:editaction:reorder")],
        ]
    )
    await update.effective_message.reply_text(
        f"Split: {split['split_name']}\nPilih tindakan:", reply_markup=markup
    )
    return EDIT_ACTION


async def edit_split_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _answer_callback(update)
    action = update.callback_query.data.rsplit(":", 1)[1]
    context.user_data["edit_action"] = action
    prompts = {
        "name": "Masukkan nama split baru:",
        "add": "Masukkan nama exercise yang ingin ditambahkan:",
        "remove": "Masukkan nomor exercise yang ingin dihapus:",
        "reorder": "Masukkan urutan baru dengan format nomor_asal nomor_tujuan, contoh: 3 1",
    }
    await update.effective_message.reply_text(prompts[action])
    return EDIT_INPUT


async def edit_split_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    split_id = context.user_data["edit_split_id"]
    action = context.user_data["edit_action"]
    value = update.effective_message.text.strip()
    try:
        if action == "name":
            if not value:
                raise ValueError("Nama split tidak boleh kosong.")
            rename_split(user_id, split_id, value)
        elif action == "add":
            if not value:
                raise ValueError("Nama exercise tidak boleh kosong.")
            add_exercise_to_split(user_id, split_id, value)
        elif action == "remove":
            if not value.isdigit() or not remove_exercise_from_split(user_id, split_id, int(value)):
                raise ValueError("Nomor exercise tidak ditemukan.")
        elif action == "reorder":
            parts = value.split()
            if len(parts) != 2 or not all(part.isdigit() for part in parts):
                raise ValueError("Format urutan harus: nomor_asal nomor_tujuan")
            if not reorder_exercise(user_id, split_id, int(parts[0]), int(parts[1])):
                raise ValueError("Nomor posisi exercise tidak valid.")
    except Exception as error:
        await update.effective_message.reply_text(f"Gagal mengubah split: {error}")
        return ConversationHandler.END
    await update.effective_message.reply_text("Workout split berhasil diperbarui.")
    await start_command(update, context)
    return ConversationHandler.END


async def delete_split_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _answer_callback(update)
    splits = get_splits(update.effective_user.id)
    if not splits:
        await update.effective_message.reply_text("Belum ada workout split untuk dihapus.")
        return ConversationHandler.END
    markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"{index}. {split['split_name']}",
                    callback_data=f"split:deleteselect:{index}",
                )
            ]
            for index, split in enumerate(splits, start=1)
        ]
    )
    await update.effective_message.reply_text("Pilih split yang ingin dikelola:", reply_markup=markup)
    return DELETE_SELECT


async def delete_split_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _answer_callback(update)
    split_number = int(update.callback_query.data.rsplit(":", 1)[1])
    split = get_split_by_number(update.effective_user.id, split_number)
    if not split:
        await update.effective_message.reply_text("Split tidak ditemukan.")
        return ConversationHandler.END
    context.user_data["delete_split_id"] = split["id"]
    context.user_data["delete_split_number"] = split_number
    markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Hapus seluruh split", callback_data="split:deleteaction:split")],
            [InlineKeyboardButton("Hapus exercise", callback_data="split:deleteaction:exercise")],
        ]
    )
    await update.effective_message.reply_text(
        f"Split: {split['split_name']}\nPilih tindakan:", reply_markup=markup
    )
    return DELETE_ACTION


async def delete_split_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _answer_callback(update)
    action = update.callback_query.data.rsplit(":", 1)[1]
    if action == "split":
        await update.effective_message.reply_text(
            "Konfirmasi hapus split ini:",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Ya, hapus", callback_data="split:deleteconfirm")]]
            ),
        )
        return DELETE_CONFIRM
    exercises = get_split_exercises(update.effective_user.id, context.user_data["delete_split_id"])
    if not exercises:
        await update.effective_message.reply_text("Split ini belum memiliki exercise.")
        return ConversationHandler.END
    markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"{index}. {exercise['exercise_name']}",
                    callback_data=f"split:deleteexercise:{index}",
                )
            ]
            for index, exercise in enumerate(exercises, start=1)
        ]
    )
    await update.effective_message.reply_text("Pilih exercise yang ingin dihapus:", reply_markup=markup)
    return DELETE_EXERCISE_SELECT


async def delete_exercise_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _answer_callback(update)
    exercise_number = int(update.callback_query.data.rsplit(":", 1)[1])
    context.user_data["delete_exercise_number"] = exercise_number
    await update.effective_message.reply_text(
        "Konfirmasi hapus exercise ini:",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Ya, hapus", callback_data="split:deleteexerciseconfirm")]]
        ),
    )
    return DELETE_CONFIRM


async def delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _answer_callback(update)
    user_id = update.effective_user.id
    if update.callback_query.data == "split:deleteconfirm":
        deleted = delete_split(user_id, context.user_data["delete_split_id"])
        message = "Workout split berhasil dihapus." if deleted else "Split tidak ditemukan."
    else:
        deleted = remove_exercise_from_split(
            user_id,
            context.user_data["delete_split_id"],
            context.user_data["delete_exercise_number"],
        )
        message = "Exercise berhasil dihapus." if deleted else "Exercise tidak ditemukan."
    await update.effective_message.reply_text(message)
    await start_command(update, context)
    return ConversationHandler.END


async def add_split_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("Nama split tidak boleh kosong. Coba lagi:")
        return ADD_NAME
    context.user_data["new_split_name"] = name
    await update.message.reply_text(
        "Masukkan daftar exercise dipisahkan koma.\nContoh: Bench Press, Squat, Lat Pulldown"
    )
    return ADD_EXERCISES


async def add_split_exercises(update: Update, context: ContextTypes.DEFAULT_TYPE):
    exercises = [item.strip() for item in update.message.text.split(",") if item.strip()]
    if not exercises:
        await update.message.reply_text("Minimal masukkan satu exercise:")
        return ADD_EXERCISES
    context.user_data["new_exercises"] = exercises
    context.user_data["new_prs"] = []
    context.user_data["new_pr_index"] = 0
    await update.message.reply_text(
        f"PR untuk {exercises[0]} (format: berat repetisi, atau skip):"
    )
    return ADD_PR


async def add_split_pr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        pr = _parse_pr(update.message.text)
    except (ValueError, TypeError) as error:
        await update.message.reply_text(str(error))
        return ADD_PR
    exercises = context.user_data["new_exercises"]
    context.user_data["new_prs"].append(pr)
    context.user_data["new_pr_index"] += 1
    index = context.user_data["new_pr_index"]
    if index < len(exercises):
        await update.message.reply_text(
            f"PR untuk {exercises[index]} (format: berat repetisi, atau skip):"
        )
        return ADD_PR
    try:
        create_split(
            update.effective_user.id,
            context.user_data["new_split_name"],
            exercises,
            context.user_data["new_prs"],
        )
    except Exception as error:
        await update.message.reply_text(f"Gagal menyimpan split: {error}")
        return ConversationHandler.END
    await update.message.reply_text("Workout split berhasil ditambahkan!")
    await start_command(update, context)
    return ConversationHandler.END


async def edit_split_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Edit using compact commands to keep the bot usable without inline UI.

    Examples: ``/edt 1 name Push Day``, ``/edt 1 add Cable Fly``,
    ``/edt 1 remove 2``, and ``/edt 1 reorder 3 1``.
    """
    args = context.args
    if len(args) < 2 or not args[0].isdigit():
        await update.message.reply_text(
            "Gunakan:\n/edt <nomor> name <nama baru>\n"
            "/edt <nomor> add <nama exercise>\n"
            "/edt <nomor> remove <nomor exercise>\n"
            "/edt <nomor> reorder <dari> <ke>"
        )
        return
    split = get_split_by_number(update.effective_user.id, int(args[0]))
    if not split:
        await update.message.reply_text("Nomor split tidak ditemukan.")
        return
    action = args[1].lower()
    try:
        if action == "name" and len(args) >= 3:
            rename_split(update.effective_user.id, split["id"], " ".join(args[2:]))
            await update.message.reply_text("Nama split berhasil diperbarui.")
        elif action == "add" and len(args) >= 3:
            add_exercise_to_split(update.effective_user.id, split["id"], " ".join(args[2:]))
            await update.message.reply_text("Exercise berhasil ditambahkan.")
        elif action == "remove" and len(args) == 3 and args[2].isdigit():
            removed = remove_exercise_from_split(
                update.effective_user.id, split["id"], int(args[2])
            )
            await update.message.reply_text(
                "Exercise berhasil dihapus." if removed else "Nomor exercise tidak ditemukan."
            )
        elif (
            action == "reorder"
            and len(args) == 4
            and args[2].isdigit()
            and args[3].isdigit()
        ):
            moved = reorder_exercise(
                update.effective_user.id,
                split["id"],
                int(args[2]),
                int(args[3]),
            )
            await update.message.reply_text(
                "Urutan exercise berhasil diperbarui."
                if moved
                else "Nomor posisi exercise tidak valid."
            )
        else:
            await update.message.reply_text("Format `/edt` tidak valid.", parse_mode="Markdown")
    except Exception as error:
        await update.message.reply_text(f"Gagal mengubah split: {error}")


async def delete_split_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a whole split, or an exercise assignment from a split.

    Examples: ``/del 1 confirm`` and ``/del 1 exercise 2 confirm``.
    """
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text(
            "Daftar split:\n"
            + _split_list(get_splits(update.effective_user.id))
            + "\n\nGunakan /del <nomor> confirm atau "
            "/del <nomor> exercise <nomor> confirm."
        )
        return
    split = get_split_by_number(update.effective_user.id, int(args[0]))
    if not split:
        await update.message.reply_text("Nomor split tidak ditemukan.")
        return
    try:
        if (
            len(args) == 4
            and args[1].lower() == "exercise"
            and args[2].isdigit()
            and args[3].lower() == "confirm"
        ):
            removed = remove_exercise_from_split(
                update.effective_user.id, split["id"], int(args[2])
            )
            message = "Exercise berhasil dihapus." if removed else "Nomor exercise tidak ditemukan."
        elif len(args) == 2 and args[1].lower() == "confirm":
            deleted = delete_split(update.effective_user.id, split["id"])
            message = "Workout split berhasil dihapus." if deleted else "Split tidak ditemukan."
        elif len(args) == 1:
            message = (
                f"Anda akan menghapus '{split['split_name']}'. "
                f"Ulangi dengan /del {args[0]} confirm untuk melanjutkan."
            )
        elif len(args) == 3 and args[1].lower() == "exercise" and args[2].isdigit():
            message = (
                "Konfirmasi penghapusan exercise dengan: "
                f"/del {args[0]} exercise {args[2]} confirm"
            )
        else:
            message = "Format `/del` tidak valid."
        await update.message.reply_text(message, parse_mode="Markdown")
    except Exception as error:
        await update.message.reply_text(f"Gagal menghapus data: {error}")
