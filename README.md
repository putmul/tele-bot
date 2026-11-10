# GymBuddy

GymBuddy adalah sistem pencatatan kebugaran yang terdiri dari **Telegram Bot**
dan **dashboard Streamlit**. Bot digunakan untuk mencatat workout, kardio,
pengukuran tubuh, personal record (PR), serta pengingat gym. Dashboard membaca
data yang sama dari MariaDB dan menampilkannya dalam bentuk ringkasan, tabel,
dan grafik progres.

## Fitur

- Membuat, mengubah, mengurutkan, dan menghapus workout split serta exercise.
- Menjalankan sesi workout dengan navigasi exercise melalui tombol inline.
- Mencatat set, PR, estimasi 1RM (rumus Epley), dan riwayat latihan.
- Rest timer dan pengingat gym berulang menggunakan Telegram JobQueue.
- Mencatat kardio dan menghitung jarak dari kecepatan serta durasi.
- Menyimpan berat badan, tinggi badan, dan BMI.
- Melihat statistik langsung melalui bot.
- Melihat dashboard progres tubuh, aktivitas, PR, workout, dan kardio.

## Arsitektur dan struktur proyek

Bot dan dashboard tidak berkomunikasi melalui API. Keduanya mengakses database
MariaDB secara langsung.

```text
GymBuddy/
├── bot/                    # Entry point, handler Telegram, dan service bot
├── dashboard/              # Aplikasi Streamlit dan halaman visualisasi
├── database/               # Koneksi, repository, schema, dan migration
├── config/                 # Konfigurasi dari environment variable
├── requirements.txt
├── .env.example
└── README.md
```

## Requirement

- Python 3.10 atau lebih baru.
- MariaDB atau MySQL yang kompatibel dengan `mysql-connector-python`.
- Telegram Bot Token dari [@BotFather](https://t.me/BotFather).
- `pip` dan virtual environment Python.

Dependency Python tercantum di [`requirements.txt`](requirements.txt). Versi
Streamlit minimum adalah `1.36` karena aplikasi menggunakan `st.navigation` dan
`st.Page`.

## Instalasi dan konfigurasi

### 1. Buat virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Buat file environment

Salin `.env.example` menjadi `.env`, kemudian isi nilainya:

```powershell
Copy-Item .env.example .env
```

| Variable | Wajib | Keterangan | Default |
| --- | --- | --- | --- |
| `TELEGRAM_BOT_TOKEN` | Ya | Token bot dari BotFather | - |
| `DB_HOST` | Tidak | Host database | `127.0.0.1` |
| `DB_PORT` | Tidak | Port MariaDB/MySQL | `3306` |
| `DB_NAME` | Tidak | Nama database | `gymbuddy` |
| `DB_USER` | Tidak | User database | `root` |
| `DB_PASSWORD` | Tidak | Password database | kosong |
| `DEFAULT_TIMEZONE` | Tidak | Zona waktu JobQueue | `Asia/Jakarta` |
| `DASHBOARD_TELEGRAM_ID` | Ya untuk dashboard | Telegram ID numerik user yang ditampilkan | - |

`DASHBOARD_TELEGRAM_ID` bukan username Telegram. Pastikan `.env` tidak dibagikan
atau di-commit karena berisi kredensial.

### 3. Siapkan database

Untuk instalasi baru, jalankan [`database/schema.sql`](database/schema.sql)
melalui MariaDB client, phpMyAdmin, atau XAMPP:

```bash
mysql -u root -p < database/schema.sql
```

Jika database dibuat dari schema versi lama, jalankan
[`database/migrations/001_add_session_position_and_split_archive.sql`](database/migrations/001_add_session_position_and_split_archive.sql)
**hanya jika kolom tersebut belum ada**. Schema baru sudah memuat perubahan
migrasi tersebut.

### 4. Jalankan aplikasi

Jalankan bot dan dashboard di terminal terpisah dari root proyek:

```bash
# Terminal 1 - Telegram Bot
python -m bot.main

# Terminal 2 - Streamlit Dashboard
streamlit run dashboard/app.py
```

Dashboard biasanya tersedia di `http://localhost:8501`. Bot menggunakan polling
Telegram, sehingga proses bot harus tetap berjalan agar dapat menerima pesan dan
mengirim reminder.

## Perintah Telegram

### Menu dan konfigurasi split

| Command | Fungsi |
| --- | --- |
| `/home` atau `/help` | Registrasi user dan menampilkan menu utama |
| `/splits` | Membuka menu tambah, edit, dan hapus split/exercise |
| `/edt <split> name <nama>` | Mengubah nama split |
| `/edt <split> add <exercise>` | Menambah exercise ke split |
| `/edt <split> remove <nomor>` | Menghapus exercise dari split |
| `/edt <split> reorder <dari> <ke>` | Mengubah urutan exercise |
| `/del <split> confirm` | Menghapus/menonaktifkan split |
| `/del <split> exercise <nomor> confirm` | Menghapus exercise dari split |

Saat membuat split melalui `/splits`, masukkan nama split, daftar exercise
dipisahkan koma, lalu PR awal setiap exercise atau `skip`.

### Workout

| Command | Fungsi |
| --- | --- |
| `/start` | Memilih split dan memulai workout |
| `/nxt` atau `/nxt <berat> <reps>` | Menyimpan set exercise saat ini lalu berpindah |
| `/pr` atau `/pr <berat> <reps>` | Mencatat PR exercise saat ini |
| `/prv` | Kembali ke exercise sebelumnya |
| `/rst` atau `/rst <menit>` | Memulai rest timer |
| `/end` | Menyelesaikan dan menyimpan sesi workout |
| `/cancel` | Membatalkan input percakapan yang sedang berlangsung |

Contoh:

```text
/nxt 80 8
/pr 100 5
/rst 3
```

Selama workout aktif, tombol inline juga dapat digunakan untuk berpindah
exercise, mencatat PR, menjalankan timer, dan menyelesaikan sesi.

### Tracking lain

| Command | Format | Fungsi |
| --- | --- | --- |
| `/cardio` | `/cardio treadmill 6.5 20` | Simpan aktivitas, kecepatan km/jam, dan durasi menit |
| `/BMI` atau `/bmi` | Input interaktif | Simpan berat, tinggi, dan BMI |
| `/notify` | Menu interaktif | Tambah, lihat, edit, atau nonaktifkan reminder gym |
| `/stat` | - | Tampilkan total workout, durasi, set, kardio, dan PR |

## Perilaku penyimpanan workout

Input set dan PR ditampung sementara selama sesi Telegram. Data disimpan secara
atomik ketika `/end` dijalankan. Exercise yang dilewati tetap disimpan sebagai
`0 kg x 0 reps`, sehingga seluruh exercise dalam split tercatat pada sesi.
Setelah `/pr` berhasil, bot otomatis berpindah ke exercise berikutnya.

Karena buffer set berada di memori proses bot, jangan mematikan atau me-restart
bot sebelum sesi aktif diselesaikan jika ingin mempertahankan input yang belum
disimpan. Sesi aktifnya sendiri tersimpan di database.

## Dashboard

Dashboard memiliki dua halaman:

- **Dashboard** — KPI total latihan/kardio, progres tubuh, aktivitas mingguan,
  dan daftar PR terbaik.
- **Latihan & Kardio** — filter periode, riwayat aktivitas, serta grafik progres
  berat/1RM/repetisi latihan dan jarak/durasi/kecepatan kardio.

Dashboard mengambil data langsung dari database dan menggunakan cache 60 detik.
Jika data baru belum terlihat, tunggu cache berakhir atau muat ulang halaman.

## Troubleshooting singkat

- `TELEGRAM_BOT_TOKEN belum diatur`: pastikan `.env` berada di root proyek dan
  token sudah diisi.
- Gagal koneksi database: periksa service MariaDB, port, nama database, user,
  dan password pada `.env`.
- Dashboard menampilkan konfigurasi ID tidak valid: isi
  `DASHBOARD_TELEGRAM_ID` dengan angka Telegram ID, bukan username.
- Command tidak dikenali: gunakan `/home` atau `/help` untuk melihat menu.
