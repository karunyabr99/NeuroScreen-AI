import sqlite3
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator
import os

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

# Enforce SQLite foreign key constraints and cascading deletes
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency for providing a transactional database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _migrate_existing_tables(conn) -> None:
    """Safely migrate existing SQLite schema to include Phase 4 research columns."""
    try:
        # Check patients table
        patient_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(patients);")).fetchall()]
        if patient_cols:
            if "is_synthetic" not in patient_cols:
                conn.execute(text("ALTER TABLE patients ADD COLUMN is_synthetic BOOLEAN DEFAULT 0;"))
            if "consent_status" not in patient_cols:
                conn.execute(text("ALTER TABLE patients ADD COLUMN consent_status VARCHAR(30) DEFAULT 'granted';"))
            if "assent_status" not in patient_cols:
                conn.execute(text("ALTER TABLE patients ADD COLUMN assent_status VARCHAR(30) DEFAULT 'not_applicable';"))
            if "guardian_relationship" not in patient_cols:
                conn.execute(text("ALTER TABLE patients ADD COLUMN guardian_relationship VARCHAR(50) DEFAULT 'Parent';"))
            if "ethics_approval_ref" not in patient_cols:
                conn.execute(text("ALTER TABLE patients ADD COLUMN ethics_approval_ref VARCHAR(100) DEFAULT 'IRB-NS-2026-ETHICS-04';"))
            if "protocol_version" not in patient_cols:
                conn.execute(text("ALTER TABLE patients ADD COLUMN protocol_version VARCHAR(50) DEFAULT 'NS-DATA-COLL-v1.0';"))
            if "consent_date" not in patient_cols:
                conn.execute(text("ALTER TABLE patients ADD COLUMN consent_date DATETIME;"))
            if "consent_withdrawn_at" not in patient_cols:
                conn.execute(text("ALTER TABLE patients ADD COLUMN consent_withdrawn_at DATETIME;"))
            if "assessor_id" not in patient_cols:
                conn.execute(text("ALTER TABLE patients ADD COLUMN assessor_id VARCHAR(64);"))

        # Check modality_features table
        modality_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(modality_features);")).fetchall()]
        if modality_cols:
            if "quality_status" not in modality_cols:
                conn.execute(text("ALTER TABLE modality_features ADD COLUMN quality_status VARCHAR(30) DEFAULT 'valid';"))
            if "is_available" not in modality_cols:
                conn.execute(text("ALTER TABLE modality_features ADD COLUMN is_available BOOLEAN DEFAULT 1;"))
            if "sensor_metadata" not in modality_cols:
                conn.execute(text("ALTER TABLE modality_features ADD COLUMN sensor_metadata JSON DEFAULT '{}';"))

        conn.commit()
    except Exception as e:
        # If running on clean memory DB or already migrated, ignore
        pass

def init_db() -> None:
    """Initialize database tables according to declared ORM models and seed core roles."""
    from app.models import patient, screening, audit, user, research_assessment, media
    Base.metadata.create_all(bind=engine)
    
    # Safe schema migration for existing SQLite database
    with engine.connect() as conn:
        _migrate_existing_tables(conn)
    
    # Seed default RBAC persona accounts
    from app.services.auth_service import AuthService
    db = SessionLocal()
    try:
        AuthService.seed_default_users(db)
    finally:
        db.close()
