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

import re
import json
from typing import Dict, Any


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    
    # ===== TASK 1: DOCUMENT VERSIONING - Updated Seed Data for Versioning =====
    # Insert seed data with versioning structure
    with SessionLocal() as db:
        # Check if documents already exist to prevent duplicates
        existing_doc_1 = db.scalar(select(models.Document).where(models.Document.document_id == 1))
        existing_doc_2 = db.scalar(select(models.Document).where(models.Document.document_id == 2))
        
        if not existing_doc_1:
            db.execute(insert(models.Document).values(document_id=1, version=1, content=DOCUMENT_1))
        if not existing_doc_2:
            db.execute(insert(models.Document).values(document_id=2, version=1, content=DOCUMENT_2))
        db.commit()
    # ===== END TASK 1 =====
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== TASK 1: DOCUMENT VERSIONING - Enhanced Get Document with Version Support =====
@app.get("/document/{document_id}")
def get_document(
    document_id: int, version: int = None, db: Session = Depends(get_db)
) -> schemas.DocumentRead:
    """
    TASK 1: Get a document from the database. 
    If version is not specified, returns the latest version.
    If version is specified, returns that specific version.
    """
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
# ===== END TASK 1 =====


# ===== TASK 1: DOCUMENT VERSIONING - New Endpoint to List All Versions =====
@app.get("/document/{document_id}/versions")
def get_document_versions(
    document_id: int, db: Session = Depends(get_db)
) -> schemas.DocumentVersionsResponse:
    """
    TASK 1: Get all versions of a document.
    Returns list of versions with metadata for version switching in UI.
    """
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
# ===== END TASK 1 =====


# ===== TASK 1: DOCUMENT VERSIONING - New Endpoint to Create New Versions =====
@app.post("/document/{document_id}/version")
def create_new_version(
    document_id: int, 
    document: schemas.DocumentCreate, 
    db: Session = Depends(get_db)
) -> schemas.DocumentRead:
    """
    TASK 1: Create a new version of a document.
    Automatically increments version number and saves new content.
    """
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
# ===== END TASK 1 =====


# ===== TASK 1: DOCUMENT VERSIONING - New Endpoint to Update Specific Versions =====
@app.put("/document/{document_id}/version/{version}")
def update_document_version(
    document_id: int,
    version: int,
    document: schemas.DocumentUpdate,
    db: Session = Depends(get_db)
) -> schemas.DocumentRead:
    """
    TASK 1: Update a specific version of a document.
    Allows editing any existing version without creating a new one.
    """
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
# ===== END TASK 1 =====


# ===== TASK 1: DOCUMENT VERSIONING - Enhanced Save with Version Support =====
@app.post("/save/{document_id}")
def save(
    document_id: int, 
    document: schemas.DocumentBase, 
    version: int = None,
    db: Session = Depends(get_db)
):
    """
    TASK 1: Save the document to the database. 
    If version is specified, updates that version. 
    Otherwise updates the latest version.
    """
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
        "version": existing_document.version,  # Return version info
        "content": document.content
    }
# ===== END TASK 1 =====


# ===== TASK 2: REAL-TIME AI SUGGESTIONS - Enhanced WebSocket Implementation =====
@app.websocket("/ws")
async def websocket(websocket: WebSocket, ai: AI = Depends(get_ai)):
    await websocket.accept()
    print("WebSocket connection established")
    
    while True:
        try:
            # Receive HTML content from the client
            raw_document = await websocket.receive_text()
            print("Received document content via WebSocket")
            
            # Convert HTML to plain text for AI processing
            plain_text_document = strip_html_tags(raw_document)
            
            if not plain_text_document.strip():
                # Send empty suggestions if no content
                await websocket.send_text(json.dumps({
                    "type": "suggestions",
                    "data": {"issues": []},
                    "status": "success"
                }))
                continue
            
            # Send status update to client
            await websocket.send_text(json.dumps({
                "type": "status",
                "data": {"message": "Analyzing document..."},
                "status": "processing"
            }))
            
            # Stream AI suggestions
            accumulated_response = ""
            async for chunk in ai.review_document(plain_text_document):
                if chunk:
                    accumulated_response += chunk
                    
                    # Try to parse JSON incrementally
                    try:
                        # Attempt to parse the accumulated response
                        parsed_suggestions = json.loads(accumulated_response)
                        
                        # Validate the structure
                        if validate_ai_response(parsed_suggestions):
                            # Send successful suggestions to client
                            await websocket.send_text(json.dumps({
                                "type": "suggestions",
                                "data": parsed_suggestions,
                                "status": "success"
                            }))
                            break  # Successfully processed
                        
                    except json.JSONDecodeError:
                        # Continue accumulating if JSON is incomplete
                        continue
            
            # If we couldn't parse valid JSON, send error
            if not accumulated_response or not validate_ai_response_structure(accumulated_response):
                await websocket.send_text(json.dumps({
                    "type": "error", 
                    "data": {"message": "Failed to generate valid suggestions"},
                    "status": "error"
                }))
                        
        except WebSocketDisconnect:
            print("WebSocket client disconnected")
            break
        except Exception as e:
            print(f"WebSocket error occurred: {e}")
            # Send error message to client
            try:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"message": f"Processing error: {str(e)}"},
                    "status": "error"
                }))
            except:
                # If we can't send error message, connection is likely broken
                break


def strip_html_tags(html_content: str) -> str:
    """
    TASK 2: Convert HTML content to plain text for AI processing.
    The AI library expects plain text without HTML markup.
    """
    if not html_content:
        return ""
    
    # Remove HTML tags using regex
    clean_text = re.sub(r'<[^>]+>', '', html_content)
    
    # Replace HTML entities
    clean_text = clean_text.replace('&nbsp;', ' ')
    clean_text = clean_text.replace('&amp;', '&')
    clean_text = clean_text.replace('&lt;', '<')
    clean_text = clean_text.replace('&gt;', '>')
    clean_text = clean_text.replace('&quot;', '"')
    
    # Clean up whitespace
    clean_text = re.sub(r'\s+', ' ', clean_text)
    clean_text = clean_text.strip()
    
    return clean_text


def validate_ai_response(response: Dict[Any, Any]) -> bool:
    """
    TASK 2: Validate AI response structure to handle intermittent JSON formatting errors.
    """
    try:
        # Check if response has required structure
        if not isinstance(response, dict):
            return False
            
        if "issues" not in response:
            return False
            
        issues = response["issues"]
        if not isinstance(issues, list):
            return False
            
        # Validate each issue structure
        for issue in issues:
            if not isinstance(issue, dict):
                return False
                
            required_fields = ["type", "severity", "paragraph", "description", "suggestion"]
            if not all(field in issue for field in required_fields):
                return False
                
            # Validate severity values
            if issue["severity"] not in ["high", "medium", "low"]:
                return False
                
        return True
        
    except Exception:
        return False


def validate_ai_response_structure(response_text: str) -> bool:
    """
    TASK 2: Additional validation helper for response text.
    """
    try:
        parsed = json.loads(response_text)
        return validate_ai_response(parsed)
    except json.JSONDecodeError:
        return False
# ===== END TASK 2 =====