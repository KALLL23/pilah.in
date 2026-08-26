# pilah.in

pilah.in is a mobile waste-management assistant for Kota Semarang. It combines waste identification, actionable handling recommendations, facility discovery, community reporting, geospatial risk prioritisation, and map-based monitoring.

The project is in its foundation stage. The current repository structure has been aligned with the engineering blueprint; the production feature set has not yet been implemented.

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

### Backend prototype

```bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The existing backend endpoint is a temporary prototype and will be replaced in stages with the API contract defined in the engineering blueprint.

## Configuration

Copy `.env.example` to `.env` before introducing services that require configuration. Fill in secrets only in `.env`; it is ignored by Git.
