"""Start and help commands."""

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from database.connection import register_user

WELCOME_MESSAGE = """Selamat datang di GymBuddy_Bot!

Asisten pribadi untuk membantu mengelola latihan gym Anda.

Daftar Perintah:
/start - Mulai Workout
/splits - Kelola Workout Split
/notify - Atur Pengingat Gym
/stat - Statistik Workout
/cardio - Catat Cardio
/BMI - Catat Pengukuran Tubuh

Saat workout aktif, gunakan tombol navigasi di dalam pesan workout.
Gunakan tombol menu di bawah untuk navigasi."""

MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["/home", "/start", "/splits"],
        ["/notify", "/stat"],
        ["/cardio", "/BMI"],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
)


async def home_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id, user.username)
    await update.effective_message.reply_text(
        WELCOME_MESSAGE,
        reply_markup=MAIN_MENU,
    )
