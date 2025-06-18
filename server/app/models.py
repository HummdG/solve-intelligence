from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.internal.db import Base


class Document(Base):
    __tablename__ = "document"
    id = Column(Integer, primary_key=True, index=True)
    
    # ===== TASK 1: DOCUMENT VERSIONING - Database Schema Changes =====
    document_id = Column(Integer, index=True)  # Logical document ID (1, 2, etc.)
    version = Column(Integer, default=1)       # Version number for each document
    content = Column(String)
    created_at = Column(DateTime, server_default=func.now())  # Track when version was created
    
    # Ensure unique combination of document_id and version (prevents duplicate versions)
    __table_args__ = (UniqueConstraint('document_id', 'version', name='uq_document_version'),)
    # ===== END TASK 1 =====


# Include your models here, and they will automatically be created as tables in the database on start-up