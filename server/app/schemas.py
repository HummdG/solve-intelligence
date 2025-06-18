from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List


class DocumentBase(BaseModel):
    content: str


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(DocumentBase):
    pass


class DocumentRead(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    # ===== TASK 1: DOCUMENT VERSIONING - Extended Schema for Versioning =====
    document_id: int      # Logical document ID
    version: int          # Version number
    created_at: datetime  # When this version was created
    # ===== END TASK 1 =====


# ===== TASK 1: DOCUMENT VERSIONING - New Schemas for Version Management =====
class DocumentVersionInfo(BaseModel):
    """Schema for individual version information"""
    model_config = ConfigDict(from_attributes=True)
    
    version: int
    created_at: datetime


class DocumentVersionsResponse(BaseModel):
    """Schema for listing all versions of a document"""
    document_id: int
    versions: List[DocumentVersionInfo]
    latest_version: int
# ===== END TASK 1 =====