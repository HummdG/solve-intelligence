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
    document_id: int
    version: int
    created_at: datetime


class DocumentVersionInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    version: int
    created_at: datetime


class DocumentVersionsResponse(BaseModel):
    document_id: int
    versions: List[DocumentVersionInfo]
    latest_version: int