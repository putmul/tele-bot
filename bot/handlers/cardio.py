"""Cardio tracker command."""

from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.start import start_command
from database.repository import save_cardio


async def cardio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save cardio from: /cardio aktivitas kecepatan durasi."""
    args = context.args
    if len(args) < 3:
        await update.effective_message.reply_text(
            "Format cardio:\n/cardio aktivitas kecepatan durasi\n\n"
            "Contoh:\n/cardio treadmill 6.5 20"
        )
        return
    activity = " ".join(args[:-2]).strip()
    try:
        speed = float(args[-2].replace(",", "."))
        duration = float(args[-1].replace(",", "."))
        if not activity or speed <= 0 or duration <= 0:
            raise ValueError
    except ValueError:
        await update.effective_message.reply_text(
            "Input tidak valid. Contoh yang benar: /cardio treadmill 6.5 20"
        )
        return
    try:
        distance = save_cardio(update.effective_user.id, activity, speed, duration)
    except Exception as error:
        await update.effective_message.reply_text(f"Gagal menyimpan cardio: {error}")
        return
    await update.effective_message.reply_text(
        f"Cardio berhasil disimpan!\n\n"
        f"Aktivitas: {activity}\nKecepatan: {speed:g} km/j\n"
        f"Durasi: {duration:g} menit\nJarak: {distance:.2f} km"
    )
    await start_command(update, context)
