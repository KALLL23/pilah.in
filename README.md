# pilah.in

**pilah.in** adalah aplikasi mobile pengelolaan sampah untuk Kota Semarang. Aplikasi ini menggabungkan identifikasi sampah, rekomendasi penanganan, pencarian fasilitas, pelaporan komunitas, pemetaan risiko berbasis geospasial, dan pemantauan melalui peta.

Proyek ini sedang dalam tahap pengembangan aktif. Repository ini mencakup skema PostgreSQL/PostGIS, infrastruktur Docker, adapter klasifikasi dan deteksi YOLO, kontrak backend `/api/v1` yang lengkap, dan mesin rekomendasi LLM berbasis data pengetahuan.

---

## Panduan Cepat untuk Juri

### Yang Dibutuhkan

| Komponen | Keterangan |
|----------|------------|
| **Docker Desktop** | Diinstal dan dijalankan di laptop |
| **HP Android** | Terhubung ke WiFi yang sama dengan laptop |
| **OpenRouter API Key** | Gratis, daftar di https://openrouter.ai |

### Langkah 1: Menjalankan Backend (Laptop)

1. **Clone repository ini:**
   ```bash
   git clone https://github.com/KALLL23/pilah.in.git
   cd pilah.in
   ```

2. **Copy file konfigurasi:**
   ```bash
   copy .env.example .env
   ```

3. **Edit file `.env`**, isi nilai berikut (beberapa sudah diisi otomatis):
   ```
   ADMIN_EMAIL=admin@pilah.in
   ADMIN_PASSWORD=admin_password_123
   JWT_SECRET=isi-dengan-teks-acak-32-karakter
   MINIO_PUBLIC_ENDPOINT=<IP_LAPTOP_ANDA>:9000
   LLM_API_KEY=<API_KEY_DARI_OPENROUTER>
   ```
   > **Penting:** 
   > - Ganti `<IP_LAPTOP_ANDA>` dengan IP address laptop Anda. Caranya: buka Command Prompt, ketik `ipconfig`, cari IPv4 Address (biasanya `192.168.x.x`).
   > - Ganti `<API_KEY_DARI_OPENROUTER>` dengan API key dari langkah berikut.

4. **Dapatkan OpenRouter API Key** (gratis):
   - Buka https://openrouter.ai
   - Daftar/login dengan GitHub atau Google
   - Buka https://openrouter.ai/keys
   - Klik **Create Key**, beri nama bebas
   - Copy key-nya (format: `sk-or-v1-...`)
   - Paste ke file `.env` pada baris `LLM_API_KEY=`

4. **Jalankan Docker Compose:**
   ```bash
   docker compose up --build
   ```

5. **Tunggu** hingga muncul pesan:
   ```
   api-1  | {"status":"success","message":"pilah.in API is running."}
   ```

6. **Verifikasi** backend berjalan dengan membuka browser:
   ```
   http://localhost:8000/health
   ```

### Langkah 2: Menginstall Aplikasi Mobile

#### Cara A: Menggunakan APK yang Sudah Jadi (Disarankan)

1. Copy file `app-debug.apk` dari folder root repository ke HP Anda
2. Buka file APK di HP
3. Jika muncul peringatan "Unknown source", pilih **Install Anyway**

#### Cara B: Build dari Source

1. Pastikan Flutter SDK 3.35.x sudah terinstall
2. Edit file `mobile/lib/core/config/app_config.dart`:
   ```dart
   // Ganti IP ini sesuai IP laptop Anda
   static const String defaultServerUrl = 'http://192.168.1.10:8000';
   ```
3. Jalankan perintah berikut:
   ```bash
   cd mobile
   flutter pub get
   flutter build apk --debug
   ```
4. Install APK dari `mobile/build/app/outputs/flutter-apk/app-debug.apk`

### Langkah 3: Menjalankan Aplikasi

1. Buka aplikasi **pilah.in** di HP
2. **Login** dengan akun:
   - Email: `admin@pilah.in`
   - Password: `admin_password_123`
3. **Aktifkan Demo Mode** — tap tombol di pojok kanan atas layar login
   > Demo Mode mematikan pengecekan lokasi Semarang, sehingga aplikasi bisa dijalankan dari mana saja.
4. Gunakan fitur **Scan Waste** untuk mengambil foto sampah
5. Konfirmasi kategori sampah yang terdeteksi
6. Tunggu ~60-90 detik untuk mendapatkan rekomendasi daur ulang dari AI

### Catatan Penting

- **Laptop dan HP harus di WiFi yang sama** agar bisa terhubung
- **Firewall laptop** harus mengizinkan port `8000` dan `9000`
- **Rekomendasi AI** membutuhkan waktu ~60-90 detik karena menggunakan model gratis
- **Demo Mode** harus aktif jika menjalankan dari luar Semarang
- Jika ada masalah koneksi, pastikan IP di `app_config.dart` dan `.env` sudah benar

---

## Struktur Repositori

```text
pilah.in/
├── mobile/                 # Aplikasi Flutter
├── backend/
│   ├── app/                # Modul aplikasi FastAPI
│   ├── ai/                 # LLM, YOLO klasifikasi, dan YOLO deteksi
│   ├── tests/              # Test backend
│   └── requirements.txt    # Dependensi runtime backend
├── data/
│   └── semarang/           # Data seed Semarang
├── models/                 # Bobot YOLO
├── .env.example            # Template konfigurasi; jangan commit .env
├── app-debug.apk           # APK yang sudah jadi untuk install langsung
└── README.md
```

## Arsitektur

- **Mobile:** Flutter, Riverpod, go_router, Dio, Google Maps.
- **Backend:** FastAPI monolitik dengan PostgreSQL/PostGIS dan MinIO.
- **AI:** dua model YOLO lokal — klasifikasi untuk Scan Waste dan deteksi objek untuk Report Waste.
- **Rekomendasi:** API LLM eksternal kompatibel OpenAI, hanya menggunakan data pengetahuan sampah dan fasilitas yang terverifikasi.
- **Deployment:** Docker Compose di laptop/PC; aplikasi Flutter terhubung melalui jaringan lokal.

Cakupan operasional adalah Kota Semarang, Jawa Tengah, Indonesia.

## Training AI

Semua kode AI terkelompok di `backend/ai`: `llm`, `yolo_classification`, dan `yolo_detection`. Kedua pipeline YOLO dapat dijalankan dari root repository dengan satu perintah:

```powershell
python -m backend.ai.yolo_classification.src.pipeline --config backend/ai/yolo_classification/configs/pilah_cls_v0.1.yaml
python -m backend.ai.yolo_detection.src.pipeline --config backend/ai/yolo_detection/configs/pilah_det_v0.1.yaml
```

Pipeline deteksi membaca `backend/ai/raw_data/SynWasteNet`, memetakan sepuluh label sumber ke kategori delapan backend, dan melatih `yolo26n.pt`. Lihat `backend/ai/README.md` untuk gambaran ruang kerja dan README pipeline masing-masing untuk pengaturan dan opsi safe re-run.

## Perintah Lokal

### Mobile

```bash
cd mobile
flutter pub get
flutter run
```

### Full Local Stack

Stack ini menjalankan PostgreSQL/PostGIS, MinIO, membuat bucket object-storage, menerapkan semua migrasi Alembic, menyesuaikan file seed, dan menjalankan API.

```bash
copy .env.example .env
docker compose up --build
```

Default development lokal berfungsi tanpa `.env`, tetapi tidak boleh digunakan untuk lingkungan produksi.

### Backend Tanpa Docker

```bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Atur `DATABASE_HOST=localhost` saat menjalankan perintah migrasi di luar Docker:

```bash
cd backend
alembic upgrade head
alembic current
pytest
```

Buat perubahan skema masa depan dengan `alembic revision --autogenerate -m "deskripsi"`, tinjau SQL yang dihasilkan, lalu terapkan dengan `alembic upgrade head`. Jangan gunakan `Base.metadata.create_all()` untuk startup aplikasi.

## Cakupan Database

Migrasi awal mencakup identitas dan token refresh, scan sampah dan rekomendasi, pengetahuan sampah terverifikasi, fasilitas pembuangan, laporan sampah komunitas dan riwayat statusnya, serta laporan referensi geospasial Semarang.

PostgreSQL menggunakan `timestamptz` dan zona waktunya adalah `Asia/Jakarta` (UTC+7).

Backend menyediakan:

```text
POST  /api/v1/scans/infer
PATCH /api/v1/scans/{id}/confirm
POST  /api/v1/scans/{id}/recommend
GET   /api/v1/scans
GET   /api/v1/scans/{id}
GET   /api/v1/categories
GET   /api/v1/facilities
GET   /api/v1/facilities/nearby
GET   /api/v1/facilities/{id}
POST  /api/v1/reports
GET   /api/v1/reports
GET   /api/v1/reports/{id}
POST  /api/v1/reports/{id}/confirm
GET   /api/v1/map/reports
GET   /api/v1/map/facilities
GET   /api/v1/map/hotspots
GET   /api/v1/sync/report-status
GET/PATCH/POST/DELETE /api/v1/admin/*
```

Semua endpoint kecuali health, auth, dan categories memerlukan JWT. Endpoint admin juga memerlukan peran `ADMIN`. Dokumentasi OpenAPI interaktif tersedia di `/docs` saat API berjalan.

Inference menerima gambar JPEG, PNG, atau WEBP hingga 8 MB. Gambar disimpan di bucket MinIO privat dan respons API berisi presigned URL yang valid selama 15 menit.

## Konfigurasi

Copy `.env.example` menjadi `.env` sebelum menjalankan layanan yang memerlukan konfigurasi. Isi rahasia hanya di `.env`; file ini diabaikan oleh Git.

Atur `MINIO_PUBLIC_ENDPOINT` ke alamat LAN laptop (contoh `192.168.1.10:9000`) saat aplikasi Flutter dijalankan di HP. MinIO menggunakan `MINIO_ENDPOINT=minio:9000` secara internal, sementara presigned URL menggunakan endpoint publik.

`CLASSIFICATION_MODEL` digunakan oleh Scan Waste dan `DETECTION_MODEL` oleh Report Waste. Pembuatan laporan juga memerlukan empat lapisan GeoJSON di `data/semarang`. `NOMINATIM_BASE_URL`, `NOMINATIM_USER_AGENT`, dan `NOMINATIM_TIMEOUT_SECONDS` mengkonfigurasi reverse geocoding terbaik; kegagalan jaringan membuat `address` null dan tidak gagal pada laporan.

## Seed Operasional dan Kesiapan

`data/semarang/waste_knowledge.csv` dan `data/semarang/facilities.csv` secara sengaja hanya berisi header. Jangan promosikan kandidat dari `draft/data_draft` sampai diverifikasi. Kueri fasilitas publik hanya menampilkan fasilitas aktif, terverifikasi, `PUBLIC` yang menerima kategori yang diminta.

File spasial opsional adalah `city_boundary.geojson`, `waterways.geojson`, `residential.geojson`, dan `public_facilities.geojson`. File seed yang hilang atau kosong tidak akan membuat startup gagal. Endpoint list dan map mengembalikan respons kosong yang berhasil, rekomendasi pengetahuan mengembalikan `422 KNOWLEDGE_NOT_AVAILABLE` ketika tidak ada fakta yang cocok, dan `POST /reports` mengembalikan `503 SERVER_UNAVAILABLE` tanpa membuat record database atau objek sampai model deteksi dan setiap lapisan spasial siap.

## Setup MinIO dan Verifikasi

Copy template environment dan ganti alamat LAN contoh dengan alamat laptop saat ini:

```powershell
copy .env.example .env
# edit MINIO_PUBLIC_ENDPOINT=<IP_LAN_LAPTOP>:9000
docker compose up -d minio minio-init
```

Bootstrap membuat bucket `pilahin` secara idempoten dan secara eksplisit menjaga akses anonim dinonaktifkan. Konsol MinIO tersedia di `http://localhost:9001`; traffic API object menggunakan port `9000`.

Jalankan storage smoke test dari host setelah MinIO sehat:

```powershell
cd backend
python -m app.scripts.check_minio
```

Untuk port forward non-default:

```powershell
python -m app.scripts.check_minio --endpoint localhost:9100 --public-endpoint localhost:9100
```

Perintah ini memverifikasi kesiapan bucket, upload objek, penolakan akses unsigned, presigned download, dan cleanup. Perintah ini tidak akan meninggalkan objek smoke-test di bucket.

Flutter harus memperlakukan `image_url` yang dikembalikan oleh API sebagai data mentah: jangan membuat path MinIO dan jangan meletakkan kredensial MinIO di aplikasi mobile. Ketika URL kedaluwarsa, ambil detail scan lagi untuk mendapatkan URL baru. HP dan laptop harus berada di jaringan yang saling dapat diakses, dan firewall laptop harus mengizinkan port `8000` dan `9000`. Build development Android/iOS juga harus mengizinkan HTTP biasa untuk server LAN privat yang dikonfigurasi.

## Autentikasi

Backend menyediakan alur email/password JWT yang lengkap:

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me
```

Registrasi selalu membuat `USER`; klien tidak dapat mengirim atau memilih peran. Peran yang didukung hanya `USER` dan `ADMIN`. `ADMIN` awal dibuat secara idempoten dari `ADMIN_EMAIL` dan `ADMIN_PASSWORD` selama startup container.

Atur `JWT_SECRET` unik yang mengandung minimal 32 karakter. Access token kedaluwarsa setelah 30 menit dan refresh token setelah 30 hari secara default. Refresh token diputar setiap kali refresh, disimpan hanya sebagai hash SHA-256, dan dapat dibatalkan melalui logout. Flutter harus menyimpan kedua token di secure storage, hanya menggunakan access token di header `Authorization: Bearer`, dan mengganti kedua token yang disimpan setelah refresh yang berhasil.
