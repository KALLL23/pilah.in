# Backend API pilah.in

Dokumen ini adalah handoff backend untuk integrasi aplikasi mobile pilah.in. Kontrak API `/api/v1` sudah diimplementasikan, tetapi beberapa fitur sengaja belum aktif secara operasional karena dataset terverifikasi dan model detection belum tersedia.

Dokumentasi interaktif tersedia saat API berjalan:

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
- Health check: `GET http://localhost:8000/health`

## Progress saat ini

| Modul | Kontrak API | Logic backend | Data/dependency runtime | Status integrasi mobile |
|---|---:|---:|---|---|
| Authentication | Selesai | Selesai | JWT secret wajib dikonfigurasi | Siap |
| Categories | Selesai | Selesai | Delapan kategori berasal dari migration | Siap |
| Scan classification | Selesai | Selesai | `models/waste_cls.pt` tersedia; membutuhkan MinIO | Siap diuji melalui stack |
| Recommendation | Selesai | Selesai | Knowledge seed masih kosong dan LLM harus dikonfigurasi | Tangani `422` |
| Facilities | Selesai | Selesai | Facility seed masih kosong | Siap, hasil awal kosong |
| Reports | Selesai | Selesai | Detection model dan data spasial belum tersedia | Tangani `503` |
| Waste Map | Selesai | Selesai | Mengikuti facility/report yang tersedia | Siap, layer dapat kosong |
| Hotspot | Selesai | Selesai | Membutuhkan minimal tiga report aktif | Siap, hasil awal kosong |
| Admin | Selesai | Selesai | Membutuhkan akun role `ADMIN` | Siap |
| Status sync | Selesai | Selesai | Membutuhkan report milik pengguna | Siap |

Verifikasi kode terakhir:

- 53 backend tests lulus.
- 29 path muncul di OpenAPI.
- Python compilation dan validasi Docker Compose lulus.
- Docker/PostGIS smoke test belum dijalankan karena Docker Desktop pada host belum aktif.

## Base URL untuk mobile

Sesuaikan alamat berdasarkan tempat aplikasi Flutter berjalan:

```text
Android emulator : http://10.0.2.2:8000
iOS simulator    : http://localhost:8000
Physical device  : http://<IP-LAN-LAPTOP>:8000
```

Untuk physical device, laptop dan HP harus berada di jaringan yang saling terhubung. Port API `8000` dan MinIO `9000` harus dapat diakses dari HP.

## Authentication mobile

Endpoint selain health, register, login, refresh, logout, dan categories menggunakan access token:

```http
Authorization: Bearer <access_token>
```

Login dan register mengembalikan access token, refresh token, masa berlaku, dan data user:

```json
{
  "token_type": "bearer",
  "access_token": "...",
  "refresh_token": "...",
  "access_expires_in": 1800,
  "refresh_expires_in": 2592000,
  "user": {
    "id": "uuid",
    "name": "Nama User",
    "email": "user@example.com",
    "role": "USER",
    "is_active": true,
    "created_at": "2026-08-29T10:00:00+07:00",
    "updated_at": "2026-08-29T10:00:00+07:00"
  }
}
```

Aturan client:

1. Simpan access dan refresh token di secure storage.
2. Kirim access token melalui header Bearer.
3. Saat access token kedaluwarsa, panggil refresh satu kali.
4. Refresh token selalu dirotasi; ganti kedua token lama dengan response terbaru.
5. Jika refresh gagal, hapus session lokal dan arahkan pengguna ke login.
6. Jangan pernah menyimpan credential MinIO di mobile.

## Daftar endpoint

### Health dan authentication

| Method | Endpoint | Auth | Kegunaan |
|---|---|---|---|
| GET | `/health` | Tidak | Memeriksa proses API hidup |
| POST | `/api/v1/auth/register` | Tidak | Registrasi user dan membuat session |
| POST | `/api/v1/auth/login` | Tidak | Login email/password |
| POST | `/api/v1/auth/refresh` | Tidak | Rotasi access dan refresh token |
| POST | `/api/v1/auth/logout` | Tidak | Mencabut refresh token |
| GET | `/api/v1/auth/me` | JWT | Mengambil profil session aktif |

Payload register:

```json
{
  "name": "Nama User",
  "email": "user@example.com",
  "password": "minimal-8-karakter"
}
```

Payload login:

```json
{
  "email": "user@example.com",
  "password": "password"
}
```

Payload refresh dan logout:

```json
{
  "refresh_token": "..."
}
```

### Categories

| Method | Endpoint | Auth | Kegunaan |
|---|---|---|---|
| GET | `/api/v1/categories` | Tidak | Mengambil taxonomy kategori sampah |

Kode kategori yang menjadi kontrak bersama backend, model, dan mobile:

```text
PLASTIC
PAPER_CARDBOARD
GLASS
METAL
ORGANIC
TEXTILE
ELECTRONIC_SPECIAL
RESIDUAL_MIXED
```

Mobile sebaiknya mengambil label dan deskripsi dari endpoint categories, bukan menulis ulang label backend secara permanen.

### Scan Waste

| Method | Endpoint | Auth | Kegunaan |
|---|---|---|---|
| POST | `/api/v1/scans/infer` | JWT | Upload gambar dan menjalankan classification |
| PATCH | `/api/v1/scans/{scan_id}/confirm` | JWT + owner | Konfirmasi kategori dan kondisi |
| POST | `/api/v1/scans/{scan_id}/recommend` | JWT + owner | Meminta rekomendasi grounded dari LLM |
| GET | `/api/v1/scans` | JWT | Riwayat scan milik user |
| GET | `/api/v1/scans/{scan_id}` | JWT + owner | Detail scan milik user |

`POST /scans/infer` menggunakan `multipart/form-data`:

```text
image: JPEG | PNG | WEBP, maksimum 8 MB
```

Konfirmasi scan menggunakan JSON:

```json
{
  "confirmed_category": "PLASTIC",
  "is_reusable": false,
  "is_contaminated": true,
  "is_wet": false
}
```

Alur mobile yang disarankan:

```text
infer → tampilkan prediction → user confirm → recommend
```

Recommendation belum memiliki fallback. Karena knowledge seed final masih kosong, response yang diharapkan saat ini adalah:

```text
HTTP 422 KNOWLEDGE_NOT_AVAILABLE
```

Mobile perlu menampilkan state seperti “Panduan terverifikasi untuk kondisi ini belum tersedia”, bukan membuat rekomendasi sendiri.

### Facilities

| Method | Endpoint | Auth | Kegunaan |
|---|---|---|---|
| GET | `/api/v1/facilities` | JWT | Daftar facility publik |
| GET | `/api/v1/facilities/nearby` | JWT | Facility sesuai kategori, urut terdekat |
| GET | `/api/v1/facilities/{facility_id}` | JWT | Detail facility publik |

Contoh nearby query:

```http
GET /api/v1/facilities/nearby?latitude=-6.9900&longitude=110.4200&category=PLASTIC&radius_km=10&limit=20
```

Ketentuan:

- `radius_km` default `10`, maksimum `50`.
- `limit` default dan maksimum `20` untuk nearby.
- Hanya facility `verified=true`, `is_active=true`, `access_scope=PUBLIC`, dan menerima kategori tersebut yang dikirim.
- Seed facility masih kosong, sehingga `200` dengan list kosong adalah response normal.

### Community Reports

| Method | Endpoint | Auth | Kegunaan |
|---|---|---|---|
| POST | `/api/v1/reports` | JWT | Membuat laporan baru |
| GET | `/api/v1/reports` | JWT + owner | Daftar report milik user |
| GET | `/api/v1/reports/{report_id}` | JWT + owner | Detail report milik user |
| POST | `/api/v1/reports/{report_id}/confirm` | JWT | Mengonfirmasi masalah masih ada |

`POST /reports` menggunakan `multipart/form-data`:

```text
image: JPEG | PNG | WEBP, maksimum 8 MB
latitude: -90 sampai 90
longitude: -180 sampai 180
location_accuracy_m: optional, >= 0
user_description: optional, maksimum 2000 karakter
waste_volume: SMALL | MEDIUM | LARGE
standing_water: true | false
drainage_blockage: true | false
```

Backend akan menjalankan:

```text
readiness → image validation → boundary Semarang → duplicate check
→ YOLO detection → risk calculation → reverse geocoding
→ MinIO upload → database transaction
```

Status hanya dapat bergerak:

```text
REPORTED → VERIFIED → IN_PROGRESS → RESOLVED
```

Detection model `models/waste_det.pt` dan data spasial belum tersedia. Untuk saat ini create report akan mengembalikan:

```text
HTTP 503 SERVER_UNAVAILABLE
```

Response tersebut tidak membuat record report dan tidak meninggalkan object MinIO. Mobile sebaiknya mempertahankan draft form agar pengguna dapat mencoba kembali setelah backend siap.

Jika lokasi serupa sudah dilaporkan dalam radius 30 meter selama tiga hari terakhir:

```json
{
  "error": {
    "code": "POSSIBLE_DUPLICATE",
    "message": "Masalah serupa sudah dilaporkan.",
    "details": {
      "existing_report_id": "uuid"
    }
  }
}
```

Mobile dapat menawarkan tombol “Konfirmasi Masih Ada” yang memanggil endpoint confirm pada `existing_report_id`.

### Waste Map

| Method | Endpoint | Auth | Kegunaan |
|---|---|---|---|
| GET | `/api/v1/map/reports` | JWT | Report visible untuk map |
| GET | `/api/v1/map/facilities` | JWT | Facility publik untuk map |
| GET | `/api/v1/map/hotspots` | JWT | Cluster hotspot report |

Semua endpoint map mengembalikan GeoJSON `FeatureCollection`:

```json
{
  "type": "FeatureCollection",
  "features": []
}
```

Report map default berisi report `VERIFIED` dan `IN_PROGRESS`, ditambah report `REPORTED` milik user sendiri. Tambahkan `?include_resolved=true` bila layar membutuhkan report selesai.

Hotspot dihitung menggunakan report aktif 14 hari terakhir dengan `ST_ClusterDBSCAN`, radius 50 meter, dan minimal tiga report.

### Status sync

| Method | Endpoint | Auth | Kegunaan |
|---|---|---|---|
| GET | `/api/v1/sync/report-status` | JWT + owner | Mengambil perubahan status sejak waktu tertentu |

Contoh:

```http
GET /api/v1/sync/report-status?since=2026-08-29T08:00:00%2B07:00
```

Timestamp wajib memiliki timezone. Simpan `server_time` dari response sebagai cursor untuk request berikutnya. Endpoint ini disiapkan untuk Flutter WorkManager dan local notification.

### Admin reports

| Method | Endpoint | Auth | Kegunaan |
|---|---|---|---|
| GET | `/api/v1/admin/reports` | ADMIN | Daftar seluruh report; dapat difilter `status` |
| GET | `/api/v1/admin/reports/{report_id}` | ADMIN | Detail report |
| PATCH | `/api/v1/admin/reports/{report_id}/status` | ADMIN | Menjalankan satu status transition |

Payload status:

```json
{
  "status": "VERIFIED"
}
```

Melompati atau memundurkan status menghasilkan `409 INVALID_STATUS_TRANSITION`.

### Admin facilities

| Method | Endpoint | Auth | Kegunaan |
|---|---|---|---|
| GET | `/api/v1/admin/facilities` | ADMIN | Daftar termasuk inactive/unverified |
| GET | `/api/v1/admin/facilities/{facility_id}` | ADMIN | Detail internal facility |
| POST | `/api/v1/admin/facilities` | ADMIN | Membuat kandidat facility |
| PATCH | `/api/v1/admin/facilities/{facility_id}` | ADMIN | Memperbarui/verifikasi facility |
| DELETE | `/api/v1/admin/facilities/{facility_id}` | ADMIN | Soft-delete facility |

Facility baru default ke:

```text
access_scope = UNKNOWN
verified = false
is_active = true
```

Nilai `access_scope`:

```text
PUBLIC | COMMUNITY | INTERNAL | UNKNOWN
```

Facility hanya dapat diverifikasi jika koordinat, source, `last_verified_at`, dan minimal satu `accepted_categories` tersedia.

### Admin waste knowledge

| Method | Endpoint | Auth | Kegunaan |
|---|---|---|---|
| GET | `/api/v1/admin/knowledge` | ADMIN | Daftar fakta termasuk inactive |
| GET | `/api/v1/admin/knowledge/{knowledge_id}` | ADMIN | Detail fakta |
| POST | `/api/v1/admin/knowledge` | ADMIN | Menambahkan fakta atomik |
| PATCH | `/api/v1/admin/knowledge/{knowledge_id}` | ADMIN | Memperbarui fakta |
| DELETE | `/api/v1/admin/knowledge/{knowledge_id}` | ADMIN | Soft-delete fakta |

Contoh fakta:

```json
{
  "category": "PLASTIC",
  "condition_scope": {
    "is_contaminated": true,
    "is_wet": false
  },
  "content": "Satu fakta terverifikasi dan atomik.",
  "source": "Nama sumber",
  "source_url": "https://example.org/source",
  "last_reviewed_at": "2026-08-29T00:00:00+07:00",
  "is_active": true
}
```

Knowledge hanya memberi konteks ke LLM. Field final seperti action, preparation steps, dan warning tidak disimpan sebagai keputusan siap pakai pada knowledge.

## Pagination

Endpoint list menggunakan:

```text
limit
offset
```

Response umum:

```json
{
  "items": [],
  "total": 0,
  "limit": 20,
  "offset": 0
}
```

Mobile dapat menentukan `hasMore` dari `offset + items.length < total`.

## Error contract

Semua error aplikasi menggunakan bentuk yang sama:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Pesan yang dapat ditampilkan atau dipetakan oleh mobile.",
    "details": {}
  }
}
```

Error penting untuk mobile:

| HTTP | Code | Penanganan client |
|---:|---|---|
| 401 | `TOKEN_EXPIRED` | Jalankan refresh token sekali |
| 401 | `INVALID_CREDENTIALS` | Hapus session bila refresh juga gagal |
| 403 | `FORBIDDEN` | Sembunyikan/larang fitur admin |
| 404 | `RESOURCE_NOT_FOUND` | Data tidak ada atau bukan milik user |
| 409 | `SCAN_NOT_READY` | Minta user menyelesaikan confirmation |
| 409 | `POSSIBLE_DUPLICATE` | Tawarkan confirmation report lama |
| 409 | `ALREADY_CONFIRMED` | Tampilkan bahwa user sudah mengonfirmasi |
| 409 | `INVALID_STATUS_TRANSITION` | Refresh detail report admin |
| 413 | `IMAGE_TOO_LARGE` | Minta pilih/kompres gambar |
| 415 | `UNSUPPORTED_IMAGE` | Batasi picker ke JPEG, PNG, atau WEBP |
| 422 | `VALIDATION_ERROR` | Tampilkan field error dari `details.fields` |
| 422 | `KNOWLEDGE_NOT_AVAILABLE` | Tampilkan empty state recommendation |
| 502 | `RECOMMENDATION_FAILED` | Tawarkan try again |
| 503 | `SERVER_UNAVAILABLE` | Pertahankan input dan izinkan retry nanti |

## Catatan implementasi mobile

- Perlakukan `image_url` sebagai URL opaque dan sementara; jangan membangun URL MinIO sendiri.
- Saat presigned URL kedaluwarsa, panggil detail scan/report untuk memperoleh URL baru.
- Jangan menganggap list kosong sebagai error untuk facility, map, atau hotspot.
- Jangan membuat recommendation atau facility lokal sebagai fallback.
- Gunakan enum persis seperti kontrak API; label UI dapat diterjemahkan terpisah.
- Untuk request multipart, jangan menetapkan boundary secara manual; biarkan Dio membentuknya.
- Request create report yang timeout mungkin sudah tersimpan. Jika retry menghasilkan `POSSIBLE_DUPLICATE`, gunakan `existing_report_id`.
- Simpan timestamp dengan offset timezone, terutama untuk status sync.

## Urutan integrasi mobile yang disarankan

1. Authentication, secure token storage, dan refresh interceptor.
2. Categories dan enum mapping.
3. Scan infer, confirmation, history, dan detail.
4. State `KNOWLEDGE_NOT_AVAILABLE` untuk recommendation.
5. Facility list/nearby dengan empty state.
6. GeoJSON map layers dengan empty `FeatureCollection`.
7. Report form dan state `SERVER_UNAVAILABLE` sambil menunggu aset detection/spatial.
8. Report history, detail, confirmation, dan background status sync.
9. Admin report, facility, dan knowledge screens bila admin mobile masuk scope.

## Menjalankan backend

Dari root repository:

```powershell
copy .env.example .env
docker compose up --build
```

Test backend:

```powershell
cd backend
pytest tests -q -p no:cacheprovider
```

Seeder knowledge, facility, dan spatial berjalan otomatis setelah Alembic migration. File seed kosong tidak menggagalkan startup.

Lihat juga dokumentasi repository utama di [README root](../README.md).
