"""Body measurement command."""

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.handlers.start import home_command
from database.repository import save_body_measurement

BODY_WEIGHT, BODY_HEIGHT = range(2)


async def body_measurement_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("BODY MEASUREMENT\n\nMasukkan berat badan dalam kg, contoh: 70")
    return BODY_WEIGHT


async def body_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        weight = float(update.message.text.replace(",", "."))
        if weight <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Berat harus berupa angka lebih dari 0.")
        return BODY_WEIGHT
    context.user_data["body_weight"] = weight
    await update.message.reply_text("Masukkan tinggi badan dalam cm, contoh: 175")
    return BODY_HEIGHT


async def body_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        height = float(update.message.text.replace(",", "."))
        if height <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Tinggi harus berupa angka lebih dari 0.")
        return BODY_HEIGHT
    try:
        bmi = save_body_measurement(update.effective_user.id, context.user_data["body_weight"], height)
    except Exception as error:
        await update.message.reply_text(f"Gagal menyimpan measurement: {error}")
        return ConversationHandler.END
    await update.message.reply_text(f"Pengukuran berhasil disimpan!\n\nBMI: {bmi:.2f}")
    await home_command(update, context)
    return ConversationHandler.END
