import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON

from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    action = Column(String(100), nullable=False, index=True)
    actor = Column(String(100), default="clinician")
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

