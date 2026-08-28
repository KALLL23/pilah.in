# pilah.in

pilah.in is a mobile waste-management assistant for Kota Semarang. It combines waste identification, actionable handling recommendations, facility discovery, community reporting, geospatial risk prioritisation, and map-based monitoring.

The project is under active development. The repository includes the PostgreSQL/PostGIS schema, Docker infrastructure, YOLO classification pipeline, Scan Waste backend, and grounded LLM recommendation engine.

## Repository layout

```text
pilah.in/
├── mobile/                 # Flutter application
├── backend/
│   ├── app/                # FastAPI application modules
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

## Current local commands

### Mobile

```bash
cd mobile
flutter pub get
flutter run
```

### Full local stack

The stack starts PostgreSQL/PostGIS, MinIO, creates the configured object-storage bucket, applies all Alembic migrations, and then starts the API.

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

The Scan Waste backend currently provides:

```text
POST  /api/v1/scans/infer
PATCH /api/v1/scans/{id}/confirm
POST  /api/v1/scans/{id}/recommend
GET   /api/v1/scans
GET   /api/v1/scans/{id}
GET   /api/v1/categories
```

Inference accepts JPEG, PNG, or WEBP images up to 8 MB. Images are stored in the private MinIO bucket and API responses contain a presigned URL valid for 15 minutes.

## Configuration

Copy `.env.example` to `.env` before introducing services that require configuration. Fill in secrets only in `.env`; it is ignored by Git.

Set `MINIO_PUBLIC_ENDPOINT` to the laptop's LAN address (for example `192.168.1.10:9000`) when the Flutter application runs on a phone. MinIO uses `MINIO_ENDPOINT=minio:9000` internally, while presigned URLs use the public endpoint.
