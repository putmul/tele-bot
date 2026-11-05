# GymBuddy_Bot

Fondasi aplikasi Telegram Bot dan dashboard untuk membantu pencatatan aktivitas gym.

## Struktur awal

- `bot/` — Telegram Bot, command handlers, dan business services.
- `dashboard/` — Streamlit dashboard dan halaman visualisasi langsung dari database.
- `database/` — koneksi MariaDB, schema, dan konstanta database.
- `config/` — konfigurasi berbasis environment variable.

## Menjalankan project

### 1. Buat environment dan install dependency

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Siapkan konfigurasi

Salin `.env.example` menjadi `.env`, lalu isi `TELEGRAM_BOT_TOKEN`, konfigurasi MariaDB,
dan `DASHBOARD_TELEGRAM_ID` dengan Telegram ID user yang ingin ditampilkan.

### 3. Buat database

Jalankan `database/schema.sql` melalui phpMyAdmin atau client MariaDB di XAMPP.

### 4. Jalankan komponen

```bash
# Telegram Bot
python -m bot.main

# Streamlit Dashboard
streamlit run dashboard/app.py
```

Dashboard menggunakan koneksi database langsung dan tidak memerlukan server API terpisah.

## Command yang sudah diimplementasikan

- `/home` — registrasi user dan menu utama.
- `/splits` — membuat dan mengelola split, exercise, dan PR awal.
- `/start`, `/nxt`, `/prv`, `/pr`, `/end` — menjalankan dan menyelesaikan sesi workout.
- `/rst` — rest timer menggunakan Telegram JobQueue.
- `/notify` — gym reminder dengan menu tambah, edit, lihat, dan nonaktifkan.
- `/stat` — ringkasan sesi, durasi, set, dan PR.
- `/cardio` — mencatat dengan format `/cardio treadmill 6.5 20`.
- `/BMI` — menyimpan berat, tinggi, dan BMI.

Saat workout aktif, tombol inline digunakan untuk memilih split, navigasi
exercise, mencatat PR, menjalankan rest timer, dan menyelesaikan sesi. Tombol
navigasi disesuaikan dengan posisi exercise saat ini.

Menu `/add` juga menyediakan submenu tombol untuk menambah, mengedit, dan
menghapus split maupun exercise.

Input set dan PR ditampung sementara selama sesi. Data baru disimpan secara
atomik saat `/end`; exercise yang belum dilakukan disimpan sebagai `0 kg x 0`.
Setelah `/pr` berhasil, bot otomatis berpindah ke exercise berikutnya.

Dashboard Streamlit memiliki halaman Dashboard dan Workout & Cardio. Isi `DASHBOARD_TELEGRAM_ID` pada `.env` agar dashboard menampilkan data user yang sesuai.
