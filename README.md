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

## Status

Struktur dan entry point awal sudah tersedia. Handler command selain `/start`, endpoint query database, dan halaman visualisasi akan diimplementasikan pada fase berikutnya.
