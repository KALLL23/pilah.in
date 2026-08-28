from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.ai.classification import WasteClassifier
from app.api.errors import ApiError, api_error_handler, request_validation_error_handler
from app.api.v1.auth import router as auth_router
from app.api.v1.categories import router as categories_router
from app.api.v1.scans import router as scans_router
from app.core.config import get_settings
from app.services.storage import get_object_storage


@asynccontextmanager
async def lifespan(application: FastAPI):
    classifier = WasteClassifier(get_settings())
    await classifier.load()
    storage = get_object_storage()
    await storage.check_ready()
    application.state.waste_classifier = classifier
    application.state.object_storage = storage
    yield


from app.api.auth import router as auth_router

# Inisialisasi Aplikasi
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

# Endpoint 1: Pengecekan Status Server
@app.get("/api/health")

@app.get("/health")
@app.get("/api/health", include_in_schema=False)
def health_check():
    return {"status": "success", "message": "pilah.in API is running."}
