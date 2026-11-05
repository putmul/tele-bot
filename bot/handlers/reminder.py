"""Rest timer and gym reminder commands."""

from datetime import time, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.services.reminder_service import schedule_rest_timer, schedule_user_reminders
from database.repository import (
    add_reminders,
    deactivate_reminder,
    get_user_reminders,
)

REST_MINUTES, REMINDER_DAYS, REMINDER_TIME, REMINDER_EDIT_SELECT, REMINDER_EDIT_DAYS, REMINDER_EDIT_TIME, REMINDER_DELETE_SELECT = range(7)

# python-telegram-bot uses 0=Sunday through 6=Saturday for JobQueue days.
DAY_NAMES = {
    "sun": 0,
    "sunday": 0,
    "minggu": 0,
    "mon": 1,
    "monday": 1,
    "senin": 1,
    "tue": 2,
    "tuesday": 2,
    "selasa": 2,
    "wed": 3,
    "wednesday": 3,
    "rabu": 3,
    "thu": 4,
    "thursday": 4,
    "kamis": 4,
    "fri": 5,
    "friday": 5,
    "jumat": 5,
    "sat": 6,
    "saturday": 6,
    "sabtu": 6,
}
DAY_LABELS = ["Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"]


def _time_value(value):
    if isinstance(value, timedelta):
        seconds = int(value.total_seconds())
        return time((seconds // 3600) % 24, (seconds % 3600) // 60, seconds % 60)
    return value


def _time_text(value):
    value = _time_value(value)
    return value.strftime("%H:%M")


def _menu_markup():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("➕ Tambah", callback_data="reminder:add"),
                InlineKeyboardButton("✏️ Edit", callback_data="reminder:edit"),
            ],
            [
                InlineKeyboardButton("🗑 Hapus", callback_data="reminder:delete"),
                InlineKeyboardButton("📋 Lihat", callback_data="reminder:list"),
            ],
        ]
    )


def _day_selection_markup(selected, prefix="day"):
    buttons = []
    row = []
    for day, label in enumerate(DAY_LABELS):
        marker = "✅ " if day in selected else ""
        row.append(InlineKeyboardButton(f"{marker}{label}", callback_data=f"reminder:{prefix}:{day}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("Selesai memilih hari", callback_data=f"reminder:{prefix}:done")])
    return InlineKeyboardMarkup(buttons)


async def _answer_callback(update):
    if update.callback_query:
        await update.callback_query.answer()


async def rest_timer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _answer_callback(update)
    if context.args:
        try:
            minutes = float(context.args[0])
            if minutes <= 0:
                raise ValueError
            schedule_rest_timer(context, update.effective_chat.id, minutes)
            await update.effective_message.reply_text(
                f"Timer istirahat dimulai. Pengingat dalam {minutes:g} menit."
            )
            return ConversationHandler.END
        except ValueError:
            await update.effective_message.reply_text("Durasi harus berupa angka lebih dari 0.")
            return ConversationHandler.END
    await update.effective_message.reply_text("Berapa menit Anda ingin beristirahat?")
    return REST_MINUTES


async def rest_timer_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        minutes = float(update.effective_message.text.replace(",", "."))
        if minutes <= 0:
            raise ValueError
    except ValueError:
        await update.effective_message.reply_text("Masukkan durasi dalam menit, contoh: 3")
        return REST_MINUTES
    schedule_rest_timer(context, update.effective_chat.id, minutes)
    await update.effective_message.reply_text(
        f"Timer istirahat dimulai! Pengingat dalam {minutes:g} menit."
    )
    return ConversationHandler.END


def _parse_time(value):
    try:
        hour, minute = [int(item) for item in value.strip().split(":")]
        return time(hour=hour, minute=minute)
    except (ValueError, TypeError):
        raise ValueError("Format waktu tidak valid. Gunakan HH:MM, contoh: 18:30")


async def reminder_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "PENGATURAN GYM REMINDER\n\nPilih menu:", reply_markup=_menu_markup()
    )
    return ConversationHandler.END


async def reminder_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _answer_callback(update)
    context.user_data["reminder_days"] = []
    await update.effective_message.reply_text(
        "Pilih hari reminder. Tekan beberapa hari jika diperlukan:",
        reply_markup=_day_selection_markup([], "day"),
    )
    return REMINDER_DAYS


async def reminder_day_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _answer_callback(update)
    day = int(update.callback_query.data.rsplit(":", 1)[1])
    selected = context.user_data.setdefault("reminder_days", [])
    if day in selected:
        selected.remove(day)
    else:
        selected.append(day)
    await update.callback_query.edit_message_reply_markup(
        reply_markup=_day_selection_markup(selected, "day")
    )
    return REMINDER_DAYS


async def reminder_days_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _answer_callback(update)
    if not context.user_data.get("reminder_days"):
        await update.effective_message.reply_text("Pilih minimal satu hari terlebih dahulu.")
        return REMINDER_DAYS
    await update.effective_message.reply_text("Masukkan waktu dengan format HH:MM, contoh: 18:30")
    return REMINDER_TIME


async def reminder_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("Silakan pilih hari menggunakan tombol di atas.")
    return REMINDER_DAYS


async def reminder_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        reminder_time_value = _parse_time(update.effective_message.text)
        add_reminders(
            update.effective_user.id,
            context.user_data["reminder_days"],
            reminder_time_value,
        )
        schedule_user_reminders(context.application, update.effective_user.id)
    except Exception as error:
        await update.effective_message.reply_text(f"Gagal menyimpan reminder: {error}")
        return ConversationHandler.END
    await update.effective_message.reply_text("Reminder gym berhasil disimpan!")
    await update.effective_message.reply_text(
        "Pilih aksi reminder berikutnya:", reply_markup=_menu_markup()
    )
    return ConversationHandler.END


def _reminder_buttons(reminders, action):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"{DAY_LABELS[item['day_of_week']]} {_time_text(item['reminder_time'])}",
                    callback_data=f"reminder:{action}:{item['id']}",
                )
            ]
            for item in reminders
        ]
    )


async def reminder_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _answer_callback(update)
    reminders = get_user_reminders(update.effective_user.id)
    if not reminders:
        text = "Belum ada reminder aktif."
    else:
        text = "REMINDER AKTIF\n\n" + "\n".join(
            f"• {DAY_LABELS[item['day_of_week']]} {_time_text(item['reminder_time'])}"
            for item in reminders
        )
    await update.effective_message.reply_text(text, reply_markup=_menu_markup())
    return ConversationHandler.END


async def reminder_edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _answer_callback(update)
    reminders = get_user_reminders(update.effective_user.id)
    if not reminders:
        await update.effective_message.reply_text("Belum ada reminder untuk diedit.")
        return ConversationHandler.END
    await update.effective_message.reply_text(
        "Pilih reminder yang ingin diedit:", reply_markup=_reminder_buttons(reminders, "editselect")
    )
    return REMINDER_EDIT_SELECT


async def reminder_edit_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _answer_callback(update)
    reminder_id = int(update.callback_query.data.rsplit(":", 1)[1])
    context.user_data["reminder_edit_id"] = reminder_id
    context.user_data["reminder_edit_days"] = []
    await update.effective_message.reply_text(
        "Pilih hari baru:", reply_markup=_day_selection_markup([], "editday")
    )
    return REMINDER_EDIT_DAYS


async def reminder_edit_day_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _answer_callback(update)
    day = int(update.callback_query.data.rsplit(":", 1)[1])
    selected = context.user_data.setdefault("reminder_edit_days", [])
    if day in selected:
        selected.remove(day)
    else:
        selected.append(day)
    await update.callback_query.edit_message_reply_markup(
        reply_markup=_day_selection_markup(selected, "editday")
    )
    return REMINDER_EDIT_DAYS


async def reminder_edit_days_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _answer_callback(update)
    if not context.user_data.get("reminder_edit_days"):
        await update.effective_message.reply_text("Pilih minimal satu hari terlebih dahulu.")
        return REMINDER_EDIT_DAYS
    await update.effective_message.reply_text("Masukkan waktu baru dengan format HH:MM:")
    return REMINDER_EDIT_TIME


async def reminder_edit_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("Silakan pilih hari menggunakan tombol di atas.")
    return REMINDER_EDIT_DAYS


async def reminder_edit_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        reminder_time_value = _parse_time(update.effective_message.text)
        deactivate_reminder(update.effective_user.id, context.user_data["reminder_edit_id"])
        add_reminders(
            update.effective_user.id,
            context.user_data["reminder_edit_days"],
            reminder_time_value,
        )
        schedule_user_reminders(context.application, update.effective_user.id)
    except Exception as error:
        await update.effective_message.reply_text(f"Gagal mengubah reminder: {error}")
        return ConversationHandler.END
    await update.effective_message.reply_text("Reminder berhasil diubah.")
    await update.effective_message.reply_text(
        "Pilih aksi reminder berikutnya:", reply_markup=_menu_markup()
    )
    return ConversationHandler.END


async def reminder_delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _answer_callback(update)
    reminders = get_user_reminders(update.effective_user.id)
    if not reminders:
        await update.effective_message.reply_text("Belum ada reminder untuk dihapus.")
        return ConversationHandler.END
    await update.effective_message.reply_text(
        "Pilih reminder yang ingin dinonaktifkan:",
        reply_markup=_reminder_buttons(reminders, "deleteselect"),
    )
    return REMINDER_DELETE_SELECT


async def reminder_delete_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _answer_callback(update)
    reminder_id = int(update.callback_query.data.rsplit(":", 1)[1])
    deleted = deactivate_reminder(update.effective_user.id, reminder_id)
    schedule_user_reminders(context.application, update.effective_user.id)
    await update.effective_message.reply_text(
        "Reminder berhasil dinonaktifkan." if deleted else "Reminder tidak ditemukan.",
        reply_markup=_menu_markup(),
    )
    return ConversationHandler.END
