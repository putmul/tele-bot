"""Cardio tracker command."""

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.handlers.start import home_command
from database.repository import save_cardio

CARDIO_INPUT = 0


def _parse_cardio(value):
    parts = value.split()
    if len(parts) < 3:
        raise ValueError("Format: aktivitas kecepatan durasi, contoh: treadmill 6.5 20")
    activity = " ".join(parts[:-2]).strip()
    try:
        speed = float(parts[-2].replace(",", "."))
        duration = float(parts[-1].replace(",", "."))
    except ValueError as error:
        raise ValueError("Kecepatan dan durasi harus berupa angka.") from error
    if not activity or speed <= 0 or duration <= 0:
        raise ValueError("Aktivitas, kecepatan, dan durasi harus valid.")
    return activity, speed, duration


async def _save_cardio(update: Update, context: ContextTypes.DEFAULT_TYPE, value):
    try:
        activity, speed, duration = _parse_cardio(value)
        distance = save_cardio(update.effective_user.id, activity, speed, duration)
    except ValueError as error:
        await update.effective_message.reply_text(str(error))
        return CARDIO_INPUT
    except Exception as error:
        await update.effective_message.reply_text(f"Gagal menyimpan cardio: {error}")
        return ConversationHandler.END
    await update.effective_message.reply_text(
        f"Cardio berhasil disimpan!\n\n"
        f"Aktivitas: {activity}\nKecepatan: {speed:g} km/j\n"
        f"Durasi: {duration:g} menit\nJarak: {distance:.2f} km"
    )
    await home_command(update, context)
    return ConversationHandler.END


async def cardio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Accept direct args or open a one-line input prompt from the button."""
    if context.args:
        return await _save_cardio(update, context, " ".join(context.args))
    await update.effective_message.reply_text(
        "Masukkan cardio dalam satu baris:\n"
        "aktivitas kecepatan durasi\n\n"
        "Contoh: treadmill 6.5 20"
    )
    return CARDIO_INPUT


async def cardio_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _save_cardio(update, context, update.effective_message.text)
