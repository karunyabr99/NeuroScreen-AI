from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.api.deps import get_db
from app.core.config import settings
from app.services.ml_bridge import MLBridge

router = APIRouter()

@router.get("/health", summary="System Health & Diagnostic Status")
def health_check(db: Session = Depends(get_db)):
    # 1. Database check
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    # 2. ML Engine model status check
    models = MLBridge.get_registered_models()
    calibrated_models = [m["model_name"] for m in models if m["is_calibrated"]]

    return {
        "status": "healthy" if db_ok else "degraded",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": {
            "connected": db_ok,
            "engine": "SQLite (SQLAlchemy)"
        },
        "ml_engine": {
            "registered_models_count": len(models),
            "calibrated_models": calibrated_models,
            "modular_mode": "Active (Uncalibrated fallback enabled)"
        },
        "clinical_disclaimer": settings.CLINICAL_DISCLAIMER
    }

