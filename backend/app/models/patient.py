import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import relationship

from app.core.database import Base

class Patient(Base):
    """
    De-identified Participant Profile for Clinical Research & Screening Support.
    Strictly de-identified (no names, telephone numbers, addresses, or national IDs).
    Governed by the De-identified Research Identifier Scheme.
    """
    __tablename__ = "patients"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    anonymized_id = Column(String(64), unique=True, index=True, nullable=False)
    age_months = Column(Integer, nullable=False)
    biological_sex = Column(String(20), nullable=False)
    referral_source = Column(String(100), default="Clinic")
    clinical_notes = Column(Text, nullable=True)
    
    # Research Governance & Consent (Phase 4 Module 2)
    is_synthetic = Column(Boolean, default=False, nullable=False, index=True)
    consent_status = Column(String(30), default="pending", nullable=False) # "granted", "pending", "withdrawn", "declined"
    assent_status = Column(String(30), default="not_applicable", nullable=False) # "granted", "declined", "not_applicable"
    guardian_relationship = Column(String(50), nullable=True) # "Parent", "Legal Guardian", "Authorized Foster Caregiver"
    ethics_approval_ref = Column(String(100), default="IRB-NS-2026-ETHICS-04", nullable=False)
    protocol_version = Column(String(50), default="NS-DATA-COLL-v1.0", nullable=False)
    consent_date = Column(DateTime, nullable=True)
    consent_withdrawn_at = Column(DateTime, nullable=True)
    assessor_id = Column(String(64), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    screenings = relationship("ScreeningSession", back_populates="patient", cascade="all, delete-orphan")
    assessments = relationship("ResearchAssessment", back_populates="patient", cascade="all, delete-orphan")
    media_uploads = relationship("MediaUpload", back_populates="patient", cascade="all, delete-orphan")
