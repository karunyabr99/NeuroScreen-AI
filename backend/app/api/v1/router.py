from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, patients, screenings, multimodal, explainability, research, media, simulation, research_ml

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health & Status"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & RBAC"])
api_router.include_router(patients.router, prefix="/patients", tags=["Patients Intake"])
api_router.include_router(screenings.router, prefix="/screenings", tags=["Multimodal Screenings"])
api_router.include_router(multimodal.router, prefix="/multimodal", tags=["Multimodal Extraction"])
api_router.include_router(explainability.router, prefix="/explainability", tags=["Explainability & Models"])
api_router.include_router(research.router, prefix="/research", tags=["Research Governance & Dataset Management"])
api_router.include_router(media.router, prefix="/media", tags=["Real Video & Image Behavioral Analysis"])
api_router.include_router(simulation.router, prefix="/simulation", tags=["Child Screening Simulation Engine"])
api_router.include_router(research_ml.router, prefix="/ml", tags=["Research Machine Learning (Paper 1 & Paper 2)"])
