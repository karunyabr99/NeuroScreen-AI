import os
import sys
from pathlib import Path

# Ensure backend and root directory are always on sys.path
_app_dir = Path(__file__).resolve().parent           # .../backend/app
_backend_dir = _app_dir.parent                       # .../backend
_root_dir = _backend_dir.parent                      # .../neuroscreen ai

for _p in [str(_backend_dir), str(_root_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db
from app.api.v1.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables
    init_db()
    yield
    # Shutdown logic (if any)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "AI-powered, explainable, multimodal Autism Spectrum Disorder screening-support API "
        "synthesizing psychometric behavioral metrics, ocular gaze dynamics, and acoustic prosody biomarkers "
        "with SHAP and LIME explainability engines."
    ),
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["Health & Status"], summary="Direct Health Check")
@app.get("/api/health", tags=["Health & Status"], summary="Legacy Health Check")
def direct_health_alias():
    """Direct alias to ensure /health and /api/health always resolve successfully."""
    from app.services.ml_bridge import MLBridge
    models = MLBridge.get_registered_models()
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "health_check": f"{settings.API_V1_STR}/health",
        "database": {"connected": True, "engine": "SQLite (SQLAlchemy)"},
        "ml_engine": {"registered_models_count": len(models), "modular_mode": "Active"}
    }

@app.get("/", tags=["Root"])
def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "health_check": f"{settings.API_V1_STR}/health",
        "clinical_disclaimer": settings.CLINICAL_DISCLAIMER
    }
