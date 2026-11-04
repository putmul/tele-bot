# GymBuddy_Bot

Fondasi aplikasi Telegram Bot dan dashboard untuk membantu pencatatan aktivitas gym.

## Struktur awal

- `bot/` — Telegram Bot, command handlers, dan business services.
- `backend/` — Flask API untuk dashboard.
- `dashboard/` — Streamlit dashboard dan halaman visualisasi.
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

Salin `.env.example` menjadi `.env`, lalu isi `TELEGRAM_BOT_TOKEN` dan konfigurasi MariaDB.

### 3. Buat database

Jalankan `database/schema.sql` melalui phpMyAdmin atau client MariaDB di XAMPP.

### 4. Jalankan komponen

```bash
# Telegram Bot
python -m bot.main

# Flask API
python -m backend.app

# Streamlit Dashboard
streamlit run dashboard/app.py
```

Endpoint pengecekan API tersedia di `GET /health`.

## Command yang sudah diimplementasikan

- `/start` — registrasi user dan menu bantuan.
- `/add` — membuat split, menambahkan exercise, dan PR awal melalui percakapan.
- `/edt` — mengubah nama split, menambah/menghapus exercise, dan mengatur urutan.
- `/del` — menghapus split atau exercise assignment dengan konfirmasi.
- `/swo`, `/nxt`, `/prv`, `/pr`, `/end` — menjalankan dan menyelesaikan sesi workout.
- `/rst` — rest timer menggunakan Telegram JobQueue.
- `/ntf` — gym reminder dengan menu tambah, edit, lihat, dan nonaktifkan.
- `/stat` — ringkasan sesi, durasi, set, dan PR.
- `/cardio` — mencatat dengan format `/cardio treadmill 6.5 20`.
- `/bbbt` — menyimpan berat, tinggi, dan BMI.

Saat workout aktif, tombol inline digunakan untuk memilih split, navigasi
exercise, mencatat PR, menjalankan rest timer, dan menyelesaikan sesi. Tombol
navigasi disesuaikan dengan posisi exercise saat ini.

Menu `/add` juga menyediakan submenu tombol untuk menambah, mengedit, dan
menghapus split maupun exercise.

Input set dan PR ditampung sementara selama sesi. Data baru disimpan secara
atomik saat `/end`; exercise yang belum dilakukan disimpan sebagai `0 kg x 0`.
Setelah `/pr` berhasil, bot otomatis berpindah ke exercise berikutnya.

Antarmuka Streamlit belum dikembangkan lebih lanjut sesuai prioritas implementasi saat ini. Endpoint Flask dan halaman dashboard masih berupa fondasi untuk tahap berikutnya.
