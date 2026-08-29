# pilah.in

pilah.in is a mobile waste-management assistant for Kota Semarang. It combines waste identification, actionable handling recommendations, facility discovery, community reporting, geospatial risk prioritisation, and map-based monitoring.

The project is under active development. The repository includes the PostgreSQL/PostGIS schema, Docker infrastructure, YOLO classification and detection adapters, the complete `/api/v1` backend contract, and a grounded LLM recommendation engine.

## Repository layout

```text
pilah.in/
├── mobile/                 # Flutter application
├── backend/
│   ├── app/                # FastAPI application modules
│   ├── ai/                 # LLM, YOLO classification, and YOLO detection
│   ├── tests/              # Backend tests
│   └── requirements.txt    # Backend runtime dependencies
├── data/
│   └── semarang/           # Versioned Semarang seed data
├── models/                 # YOLO weights (tracked with Git LFS when added)
├── .env.example            # Configuration template; never commit .env
└── README.md
```

## Planned architecture

- **Mobile:** Flutter, Riverpod, go_router, Dio, MapLibre.
- **Backend:** FastAPI monolith with PostgreSQL/PostGIS and MinIO.
- **AI:** two local YOLO models—classification for Scan Waste and object detection for Report Waste.
- **Recommendation:** an external OpenAI-compatible LLM API, grounded only in verified waste knowledge and facility data.
- **Deployment:** Docker Compose on a laptop/PC; the Flutter app connects over the local network.

The operational scope is Kota Semarang, Jawa Tengah, Indonesia.

## AI training

All AI code is grouped under `backend/ai`: `llm`, `yolo_classification`, and `yolo_detection`. Both YOLO pipelines run from the repository root with one command:

```powershell
python -m backend.ai.yolo_classification.src.pipeline --config backend/ai/yolo_classification/configs/pilah_cls_v0.1.yaml
python -m backend.ai.yolo_detection.src.pipeline --config backend/ai/yolo_detection/configs/pilah_det_v0.1.yaml
```

The detection pipeline reads `backend/ai/raw_data/SynWasteNet`, maps its ten source labels into the backend's eight-category contract, and trains `yolo26n.pt`. See `backend/ai/README.md` for the workspace overview and each pipeline README for setup and safe re-run options.

## Current local commands

### Mobile

```bash
cd mobile
flutter pub get
flutter run
```

### Full local stack

The stack starts PostgreSQL/PostGIS, MinIO, creates the configured object-storage bucket, applies all Alembic migrations, reconciles operational seed files, and then starts the API.

```bash
copy .env.example .env
docker compose up --build
```

Local development defaults work without `.env`, but must never be used for a deployed environment.

### Backend without Docker

```bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Set `DATABASE_HOST=localhost` when running migration commands outside Docker:

```bash
cd backend
alembic upgrade head
alembic current
pytest
```

Create future schema changes with `alembic revision --autogenerate -m "description"`, review the generated SQL, then apply them with `alembic upgrade head`. Do not use `Base.metadata.create_all()` for application startup.

## Database scope

The initial migration covers identity and refresh tokens, waste scans and grounded recommendations, verified waste knowledge, disposal facilities, community waste reports and their status history, and Semarang geospatial reference layers. It seeds the same eight-category taxonomy used by the AI training pipeline.

PostgreSQL uses `timestamptz` and its session timezone is `Asia/Jakarta` (UTC+7). PostgreSQL still stores instants consistently; API and database output are presented in Western Indonesian Time.

The backend provides:

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

All endpoints except health, auth, and categories require a JWT. Admin endpoints additionally require the `ADMIN` role. Interactive OpenAPI documentation is available at `/docs` while the API is running.

Inference accepts JPEG, PNG, or WEBP images up to 8 MB. Images are stored in the private MinIO bucket and API responses contain a presigned URL valid for 15 minutes.

## Configuration

Copy `.env.example` to `.env` before introducing services that require configuration. Fill in secrets only in `.env`; it is ignored by Git.

Set `MINIO_PUBLIC_ENDPOINT` to the laptop's LAN address (for example `192.168.1.10:9000`) when the Flutter application runs on a phone. MinIO uses `MINIO_ENDPOINT=minio:9000` internally, while presigned URLs use the public endpoint.

`CLASSIFICATION_MODEL` is used by Scan Waste and `DETECTION_MODEL` by Report Waste. Report creation also requires all four GeoJSON layers under `data/semarang`. `NOMINATIM_BASE_URL`, `NOMINATIM_USER_AGENT`, and `NOMINATIM_TIMEOUT_SECONDS` configure best-effort reverse geocoding; network failure leaves `address` null and does not fail the report.

## Operational seed and readiness

`data/semarang/waste_knowledge.csv` and `data/semarang/facilities.csv` intentionally contain headers only. Do not promote candidates from `draft/data_draft` until they are verified. Public facility queries only expose active, verified, `PUBLIC` facilities that accept the requested category.

The optional spatial files are `city_boundary.geojson`, `waterways.geojson`, `residential.geojson`, and `public_facilities.geojson`. Missing or empty seed files do not fail startup. List and map endpoints return empty successful responses, knowledge recommendation returns `422 KNOWLEDGE_NOT_AVAILABLE` when no fact matches, and `POST /reports` returns `503 SERVER_UNAVAILABLE` without creating a database record or object until the detection model and every spatial layer are ready.

## MinIO setup and verification

Copy the environment template and replace the example LAN address with the laptop's current address:

```powershell
copy .env.example .env
# edit MINIO_PUBLIC_ENDPOINT=<LAPTOP_LAN_IP>:9000
docker compose up -d minio minio-init
```

The bootstrap creates the `pilahin` bucket idempotently and explicitly keeps anonymous access disabled. The MinIO console is available at `http://localhost:9001`; object API traffic uses port `9000`.

Run the storage smoke test from the host after MinIO is healthy:

```powershell
cd backend
python -m app.scripts.check_minio
```

For a non-default forwarded port:

```powershell
python -m app.scripts.check_minio --endpoint localhost:9100 --public-endpoint localhost:9100
```

The command verifies bucket readiness, object upload, rejection of unsigned access, presigned download, and cleanup. It never leaves the smoke-test object in the bucket.

Flutter must treat `image_url` returned by the API as opaque: do not construct MinIO paths and never put MinIO credentials in the mobile application. When a URL expires, fetch the scan detail again to receive a new URL. The phone and laptop must be on a mutually reachable network, and the laptop firewall must allow ports `8000` and `9000`. Android/iOS development builds must also permit plain HTTP for the configured private-LAN server.

## Authentication

The backend exposes the complete email/password JWT flow:

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me
```

Registration always creates a `USER`; clients cannot submit or select a role. The only supported roles are `USER` and `ADMIN`. The initial `ADMIN` is created idempotently from `ADMIN_EMAIL` and `ADMIN_PASSWORD` during container startup.

Set a unique `JWT_SECRET` containing at least 32 characters. Access tokens expire after 30 minutes and refresh tokens after 30 days by default. Refresh tokens are rotated on every refresh, stored only as SHA-256 hashes, and may be revoked through logout. Flutter should keep both tokens in secure storage, use only the access token in the `Authorization: Bearer` header, and replace both stored tokens after a successful refresh.
