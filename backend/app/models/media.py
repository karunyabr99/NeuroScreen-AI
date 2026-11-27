import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship

from app.core.database import Base

class MediaUpload(Base):
    """
    Child video or image upload record linked to a de-identified research participant.
    Stored in private secure storage with strict role-based access.
    Never exposed publicly. Media is never used for ML training without separate explicit authorization.
    """
    __tablename__ = "media_uploads"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(36), ForeignKey("screening_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    
    media_type = Column(String(20), nullable=False) # "video" or "image"
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False) # Path inside storage/media/
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    
    duration_seconds = Column(Float, nullable=True) # for video
    resolution_width = Column(Integer, nullable=True)
    resolution_height = Column(Integer, nullable=True)
    fps = Column(Float, nullable=True) # for video
    
    task_context = Column(String(100), default="structured_joint_attention", nullable=False) # structured_joint_attention, toy_play, free_movement, classroom
    media_quality_status = Column(String(30), default="validated_adequate", nullable=False) # validated_high, validated_adequate, degraded_lighting, low_resolution, motion_blurred, rejected_quality
    
    # Ethics & ML Training Authorization (Module 1 Safeguard)
    media_training_authorized = Column(Boolean, default=False, nullable=False)
    is_synthetic = Column(Boolean, default=False, nullable=False)
    uploader_id = Column(String(64), nullable=False)
    uploader_role = Column(String(50), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    patient = relationship("Patient", back_populates="media_uploads")
    session = relationship("ScreeningSession")
    analysis = relationship("MediaAnalysis", back_populates="media", uselist=False, cascade="all, delete-orphan")


class MediaAnalysis(Base):
    """
    Observable computer-vision behavioral features extracted from video or image.
    Strictly conforms to negative clinical constraints:
    - Never infers autism from facial appearance, identity, or emotion.
    - Never diagnoses autism or assigns autism severity from photographs or videos.
    - Never claims ordinary webcam tracking is equivalent to infrared eye tracking.
    """
    __tablename__ = "media_analyses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    media_id = Column(String(36), ForeignKey("media_uploads.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    pipeline_version = Column(String(50), default="cv-behavioral-v1.0", nullable=False)
    analysis_status = Column(String(30), default="completed", nullable=False) # completed, partial, failed
    data_quality_score = Column(Float, default=0.90, nullable=False)

    # Observable Task-Specific Behavioral Feature Domains (JSON)
    movement_and_pose = Column(JSON, default=dict, nullable=False)
    gesture_and_actions = Column(JSON, default=dict, nullable=False)
    gaze_measurements = Column(JSON, default=dict, nullable=False)
    joint_attention_observations = Column(JSON, default=dict, nullable=False)
    repetitive_movements = Column(JSON, default=dict, nullable=False)
    social_interaction_opportunities = Column(JSON, default=dict, nullable=False)
    
    # Image-specific context & quality (if photo)
    image_quality_and_context = Column(JSON, default=dict, nullable=False)
    
    # Ethical and Scientific Safeguard Flags
    ethical_safeguards = Column(JSON, default=dict, nullable=False)
    limitations_summary = Column(Text, nullable=True)
    clinical_recommendation = Column(Text, default="Direct in-person multidisciplinary clinical evaluation (e.g., ADOS-2, ADI-R) by qualified licensed specialists is required.", nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    media = relationship("MediaUpload", back_populates="analysis")

