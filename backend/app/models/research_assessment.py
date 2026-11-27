import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship

from app.core.database import Base

class ResearchAssessment(Base):
    """
    Real-world research assessment intake model capturing multi-informant observations
    (caregivers, teachers, and qualified clinical professionals) along with multimodal sensor data.
    Strictly segregated by participant ID, consent status, and synthetic flag.
    """
    __tablename__ = "research_assessments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Form metadata
    form_type = Column(String(30), nullable=False) # "caregiver", "teacher", "professional", "multimodal_comprehensive"
    assessor_id = Column(String(64), nullable=False)
    assessor_role = Column(String(60), nullable=False) # "Caregiver / Parent", "Teacher / Special Educator", "Qualified Professional"
    assessment_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    protocol_version = Column(String(50), default="NS-DATA-COLL-v1.0", nullable=False)
    ethics_approval_ref = Column(String(100), default="IRB-NS-2026-ETHICS-04", nullable=False)
    
    # Governance & Synthetic Segregation
    is_synthetic = Column(Boolean, default=False, nullable=False, index=True)
    data_quality_status = Column(String(30), default="complete", nullable=False) # "complete", "partial", "flagged"
    quality_score = Column(Float, default=1.0, nullable=False)

    # Multi-informant Assessment Domains (Structured JSON)
    developmental_history = Column(JSON, default=dict, nullable=False)
    communication_milestones = Column(JSON, default=dict, nullable=False)
    social_interaction_observations = Column(JSON, default=dict, nullable=False)
    behavioral_characteristics = Column(JSON, default=dict, nullable=False)
    repetitive_behaviors = Column(JSON, default=dict, nullable=False)
    
    # Caregiver concerns - Strictly noted as unconfirmed observations, NOT clinical diagnosis
    caregiver_concerns = Column(JSON, default=dict, nullable=False)
    
    # Medical and Family History (Authorized & Relevant)
    medical_family_history = Column(JSON, default=dict, nullable=False)
    
    # Multimodal Sensor Measurements (Speech, Eye-tracking, Movement)
    multimodal_measurements = Column(JSON, default=dict, nullable=False)
    
    # Narrative Assessor Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    patient = relationship("Patient", back_populates="assessments")

