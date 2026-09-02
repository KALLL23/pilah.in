# pilah.in

pilah.in adalah aplikasi pengelolaan sampah untuk Kota Semarang. Pengguna dapat memindai jenis sampah, melihat saran penanganan, mencari fasilitas terdekat, dan membuat laporan sampah di lingkungan sekitar.

Repository ini berisi aplikasi Flutter, API FastAPI, database PostgreSQL/PostGIS, serta model YOLO untuk klasifikasi dan deteksi sampah.

---

## Instalasi

### Prasyarat

Siapkan [Git](https://git-scm.com/), [Docker Desktop](https://www.docker.com/products/docker-desktop/), Flutter SDK yang mendukung Dart 3.9, serta perangkat Android atau emulator. Fitur rekomendasi juga memerlukan API key dari [OpenRouter](https://openrouter.ai/keys).

Jika aplikasi dijalankan di HP fisik, pastikan HP dan komputer terhubung ke jaringan yang sama.

### Menjalankan backend

Clone repository, lalu masuk ke direktori proyek:

```bash
git clone https://github.com/KALLL23/pilah.in.git
cd pilah.in
```

Salin template konfigurasi menjadi `.env`:

```powershell
Copy-Item .env.example .env
```

Untuk macOS atau Linux, gunakan `cp .env.example .env`.

Buka `.env`, lalu lengkapi konfigurasi berikut:

```dotenv
JWT_SECRET=<teks-acak-minimal-32-karakter>
ADMIN_EMAIL=<email-admin>
ADMIN_PASSWORD=<password-admin>
MINIO_PUBLIC_ENDPOINT=<IP-LAN-komputer>:9000
LLM_API_KEY=<API-key-OpenRouter>
```

Alamat IP LAN dapat dilihat dengan menjalankan `ipconfig` di Windows atau `ifconfig` di macOS dan Linux. `ADMIN_EMAIL` dan `ADMIN_PASSWORD` boleh dikosongkan jika akun admin awal tidak dibutuhkan.

Jalankan seluruh layanan dengan Docker Compose:

```bash
docker compose up --build
```

Backend siap digunakan ketika endpoint berikut mengembalikan status sukses:

```text
http://localhost:8000/health
```

Dokumentasi API tersedia di `http://localhost:8000/docs`.

### Menjalankan aplikasi Android

Dari direktori root proyek, jalankan:

```bash
cd mobile
flutter pub get
flutter run
```

Pada halaman login, buka pengaturan server dan masukkan alamat backend menggunakan IP LAN komputer, misalnya:

```text
http://192.168.1.10:8000
```

Untuk membuat APK debug:

```bash
flutter build apk --debug
```

File hasil build berada di `mobile/build/app/outputs/flutter-apk/app-debug.apk`.

Jika aplikasi tidak dapat terhubung, periksa kembali alamat server dan pastikan firewall mengizinkan koneksi ke port `8000` dan `9000`.

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
