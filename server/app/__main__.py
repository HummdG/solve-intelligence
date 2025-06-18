from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import insert, select, update, delete, func, desc
from sqlalchemy.orm import Session

from app.internal.ai import AI, get_ai
from app.internal.data import DOCUMENT_1, DOCUMENT_2
from app.internal.db import Base, SessionLocal, engine, get_db

import app.models as models
import app.schemas as schemas


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    # Insert seed data with versioning
    with SessionLocal() as db:
        # Check if documents already exist
        existing_doc_1 = db.scalar(select(models.Document).where(models.Document.document_id == 1))
        existing_doc_2 = db.scalar(select(models.Document).where(models.Document.document_id == 2))
        
        if not existing_doc_1:
            db.execute(insert(models.Document).values(document_id=1, version=1, content=DOCUMENT_1))
        if not existing_doc_2:
            db.execute(insert(models.Document).values(document_id=2, version=1, content=DOCUMENT_2))
        db.commit()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/document/{document_id}")
def get_document(
    document_id: int, version: int = None, db: Session = Depends(get_db)
) -> schemas.DocumentRead:
    """Get a document from the database. If version is not specified, returns the latest version."""
    if version is None:
        # Get the latest version
        document = db.scalar(
            select(models.Document)
            .where(models.Document.document_id == document_id)
            .order_by(desc(models.Document.version))
        )
    else:
        # Get specific version
        document = db.scalar(
            select(models.Document)
            .where(models.Document.document_id == document_id)
            .where(models.Document.version == version)
        )
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document


@app.get("/document/{document_id}/versions")
def get_document_versions(
    document_id: int, db: Session = Depends(get_db)
) -> schemas.DocumentVersionsResponse:
    """Get all versions of a document."""
    versions = db.scalars(
        select(models.Document)
        .where(models.Document.document_id == document_id)
        .order_by(desc(models.Document.version))
    ).all()
    
    if not versions:
        raise HTTPException(status_code=404, detail="Document not found")
    
    version_info = [
        schemas.DocumentVersionInfo(version=v.version, created_at=v.created_at)
        for v in versions
    ]
    
    return schemas.DocumentVersionsResponse(
        document_id=document_id,
        versions=version_info,
        latest_version=max(v.version for v in versions)
    )


@app.post("/document/{document_id}/version")
def create_new_version(
    document_id: int, 
    document: schemas.DocumentCreate, 
    db: Session = Depends(get_db)
) -> schemas.DocumentRead:
    """Create a new version of a document."""
    # Get the latest version number
    latest_version = db.scalar(
        select(func.max(models.Document.version))
        .where(models.Document.document_id == document_id)
    )
    
    if latest_version is None:
        # This is the first version of a new document
        new_version = 1
    else:
        new_version = latest_version + 1
    
    # Create new version
    new_document = models.Document(
        document_id=document_id,
        version=new_version,
        content=document.content
    )
    db.add(new_document)
    db.commit()
    db.refresh(new_document)
    
    return new_document


@app.put("/document/{document_id}/version/{version}")
def update_document_version(
    document_id: int,
    version: int,
    document: schemas.DocumentUpdate,
    db: Session = Depends(get_db)
) -> schemas.DocumentRead:
    """Update a specific version of a document."""
    existing_document = db.scalar(
        select(models.Document)
        .where(models.Document.document_id == document_id)
        .where(models.Document.version == version)
    )
    
    if not existing_document:
        raise HTTPException(status_code=404, detail="Document version not found")
    
    existing_document.content = document.content
    db.commit()
    db.refresh(existing_document)
    
    return existing_document


@app.post("/save/{document_id}")
def save(
    document_id: int, 
    document: schemas.DocumentBase, 
    version: int = None,
    db: Session = Depends(get_db)
):
    """Save the document to the database. If version is specified, updates that version. Otherwise updates the latest version."""
    if version is None:
        # Get the latest version
        existing_document = db.scalar(
            select(models.Document)
            .where(models.Document.document_id == document_id)
            .order_by(desc(models.Document.version))
        )
    else:
        # Get specific version
        existing_document = db.scalar(
            select(models.Document)
            .where(models.Document.document_id == document_id)
            .where(models.Document.version == version)
        )
    
    if not existing_document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    existing_document.content = document.content
    db.commit()
    
    return {
        "document_id": document_id,
        "version": existing_document.version,
        "content": document.content
    }


@app.websocket("/ws")
async def websocket(websocket: WebSocket, ai: AI = Depends(get_ai)):
    await websocket.accept()
    while True:
        try:
            """
            The AI doesn't expect to receive any HTML.
            You can call ai.review_document to receive suggestions from the LLM.
            Remember, the output from the LLM will not be deterministic, so you may want to validate the output before sending it to the client.
            """
            document = await websocket.receive_text()
            print("Received data via websocket")
        except WebSocketDisconnect:
            break
        except Exception as e:
            print(f"Error occurred: {e}")
            continue