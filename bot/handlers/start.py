"""Start and help commands."""

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from database.connection import register_user

WELCOME_MESSAGE = """Selamat datang di GymBuddy_Bot!

Asisten pribadi untuk membantu mengelola latihan gym Anda.

Daftar Perintah:
/swo - Mulai Workout
/add - Kelola Workout Split
/ntf - Atur Pengingat Gym
/stat - Statistik Workout
/cardio - Catat Cardio
/bbbt - Catat Pengukuran Tubuh

Saat workout aktif, gunakan tombol navigasi di dalam pesan workout.
Gunakan tombol menu di bawah untuk navigasi."""

MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["/start", "/swo", "/add"],
        ["/ntf", "/stat"],
        ["/cardio", "/bbbt"],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id, user.username)
    await update.effective_message.reply_text(
        WELCOME_MESSAGE,
        reply_markup=MAIN_MENU,
    )
