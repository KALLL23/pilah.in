from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.ai.classification import WasteClassifier
from app.ai.detection import WasteDetector
from app.api.errors import ApiError, api_error_handler, request_validation_error_handler
from app.api.v1.auth import router as auth_router
from app.api.v1.admin_facilities import router as admin_facilities_router
from app.api.v1.admin_knowledge import router as admin_knowledge_router
from app.api.v1.admin_reports import router as admin_reports_router
from app.api.v1.categories import router as categories_router
from app.api.v1.facilities import router as facilities_router
from app.api.v1.maps import router as maps_router
from app.api.v1.reports import router as reports_router
from app.api.v1.scans import router as scans_router
from app.api.v1.sync import router as sync_router
from app.core.config import get_settings
from app.services.storage import get_object_storage


@asynccontextmanager
async def lifespan(application: FastAPI):
    settings = get_settings()
    classifier = WasteClassifier(settings)
    await classifier.load()
    storage = get_object_storage()
    await storage.check_ready()
    application.state.waste_classifier = classifier
    # Detection stays lazy so a missing report model does not prevent startup.
    application.state.waste_detector = WasteDetector(settings)
    application.state.object_storage = storage
    yield


app = FastAPI(
    title="pilah.in API",
    description="Backend API untuk layanan pilah.in.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_exception_handler(ApiError, api_error_handler)
app.add_exception_handler(RequestValidationError, request_validation_error_handler)
app.include_router(auth_router)
app.include_router(scans_router)
app.include_router(categories_router)
app.include_router(facilities_router)
app.include_router(reports_router)
app.include_router(maps_router)
app.include_router(sync_router)
app.include_router(admin_reports_router)
app.include_router(admin_facilities_router)
app.include_router(admin_knowledge_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
@app.get("/api/health", include_in_schema=False)
def health_check():
    return {"status": "success", "message": "pilah.in API is running."}
