import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship

from app.core.database import Base

class ScreeningSession(Base):
    __tablename__ = "screening_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(30), default="pending", nullable=False) # pending, completed, failed
    protocol_version = Column(String(50), default="v1.0-multimodal-research")
    
    # Quantitative Risk Outputs
    composite_risk_score = Column(Float, nullable=True) # None when uncalibrated
    risk_tier = Column(String(50), default="INCONCLUSIVE_MODEL_UNCALIBRATED")
    confidence_interval = Column(JSON, nullable=True) # {"lower": 0.0, "upper": 0.0}
    
    # Model Metadata & Calibration
    model_version = Column(String(50), default="ensemble-v1.0-uncalibrated")
    is_calibrated = Column(Boolean, default=False, nullable=False)
    modalities_included = Column(JSON, default=list) # ["behavioral", "visual_gaze", "acoustic_prosody"]
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    patient = relationship("Patient", back_populates="screenings")
    features = relationship("ModalityFeature", back_populates="session", cascade="all, delete-orphan")
    explanations = relationship("ExplainabilityRecord", back_populates="session", cascade="all, delete-orphan")


class ModalityFeature(Base):
    __tablename__ = "modality_features"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("screening_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    modality_type = Column(String(40), nullable=False) # behavioral, visual_gaze, acoustic_prosody, developmental_milestones, movement_motor
    raw_metrics = Column(JSON, nullable=False, default=dict)
    extracted_features = Column(JSON, nullable=False, default=dict)
    quality_score = Column(Float, default=1.0) # Data quality / signal-to-noise ratio
    quality_status = Column(String(30), default="valid", nullable=False) # valid, degraded, incomplete, sensor_failed, not_administered
    is_available = Column(Boolean, default=True, nullable=False)
    sensor_metadata = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("ScreeningSession", back_populates="features")


class ExplainabilityRecord(Base):
    __tablename__ = "explainability_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("screening_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    method = Column(String(20), nullable=False) # SHAP, LIME, HYBRID
    base_value = Column(Float, nullable=True)
    prediction_value = Column(Float, nullable=True)
    feature_importances = Column(JSON, nullable=False, default=list) # [{feature, importance, modality, description}]
    summary_narrative = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("ScreeningSession", back_populates="explanations")

