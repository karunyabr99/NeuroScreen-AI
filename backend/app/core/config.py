from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pathlib import Path

class Settings(BaseSettings):
    PROJECT_NAME: str = "NeuroScreen AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS Origins - Explicit frontend origins; wildcard origins are strictly prohibited with credentials
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    
    # Security & JWT Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # 24 hours

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    ROOT_DIR: Path = BASE_DIR.parent
    ML_WEIGHTS_DIR: Path = ROOT_DIR / "ml_engine" / "weights"

    # Database
    DATABASE_URL: str = f"sqlite:///{Path(__file__).resolve().parent.parent.parent / 'neuroscreen.db'}"
    
    # Clinical Governance & Privacy
    ALLOW_UNCALIBRATED_FALLBACK: bool = True
    PRIVACY_FRAMEWORK_NAME: str = "De-identified Research Identifier Scheme"
    CLINICAL_DISCLAIMER: str = (
        "NeuroScreen AI is an experimental decision-support research aid. "
        "It is NOT an authorized diagnostic instrument. Clinical evaluations "
        "must be conducted by licensed psychologists or medical specialists. "
        "Institutional review board (IRB/Ethics Committee) approval, participant informed consent, "
        "and applicable privacy impact assessments are mandatory prior to clinical participant data collection."
    )

    model_config = SettingsConfigDict(case_sensitive=True, env_file=Path(__file__).resolve().parents[2] / ".env")

settings = Settings()
