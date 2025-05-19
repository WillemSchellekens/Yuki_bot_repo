from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
from datetime import datetime

from app.core.config import get_settings
from app.db.session import get_db
from app.db.models import Document, ProcessingStatus, DocumentValidation
from app.services.ocr_service import OCRService
from app.services.extraction_service import ExtractionService
from app.services.yuki_service import YukiService

settings = get_settings()
router = APIRouter()

# Initialize services
ocr_service = OCRService()
extraction_service = ExtractionService()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a document for processing.
    """
    try:
        # Save file
        file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create document record
        document = Document(
            filename=file.filename,
            original_filename=file.filename,
            file_path=file_path,
            mime_type=file.content_type,
            file_size=os.path.getsize(file_path),
            status=ProcessingStatus.PENDING
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        
        return {"document_id": document.id, "status": "pending"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{document_id}/process")
async def process_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Process a document using OCR and data extraction.
    """
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
            
        # Update status
        document.status = ProcessingStatus.PROCESSING
        db.commit()
        
        # Perform OCR
        text, confidence_scores = ocr_service.process_document(document.file_path)
        
        # Extract data
        extracted_data = extraction_service.extract_data(text, confidence_scores)
        
        # Update document with extracted data
        document.extracted_data = extracted_data.__dict__
        document.confidence_scores = confidence_scores
        document.status = ProcessingStatus.EXTRACTED
        db.commit()
        
        return {
            "document_id": document.id,
            "status": "extracted",
            "data": extracted_data.__dict__
        }
        
    except Exception as e:
        document.status = ProcessingStatus.ERROR
        document.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{document_id}/validate")
async def validate_document(
    document_id: int,
    validation_data: dict,
    db: Session = Depends(get_db)
):
    """
    Validate extracted data and prepare for Yuki upload.
    """
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
            
        # Create validation record
        validation = DocumentValidation(
            document_id=document.id,
            validated_by="user",  # TODO: Get from auth
            validation_data=validation_data
        )
        db.add(validation)
        
        # Update document status
        document.status = ProcessingStatus.VALIDATED
        db.commit()
        
        return {
            "document_id": document.id,
            "status": "validated",
            "validation_id": validation.id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{document_id}/upload-to-yuki")
async def upload_to_yuki(
    document_id: int,
    administration_id: str,
    db: Session = Depends(get_db)
):
    """
    Upload document and create accounting entry in Yuki.
    """
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
            
        if document.status != ProcessingStatus.VALIDATED:
            raise HTTPException(status_code=400, detail="Document must be validated first")
            
        # Initialize Yuki service
        yuki_service = YukiService(administration_id)
        
        # Upload document
        document_id = yuki_service.upload_document(
            document.file_path,
            {
                "name": document.original_filename,
                "description": document.extracted_data.get("description", ""),
                "date": document.extracted_data.get("invoice_date", datetime.now()),
                "type": "Invoice"
            }
        )
        
        # Create accounting entry
        booking_id = yuki_service.create_accounting_entry(
            document.extracted_data,
            document_id
        )
        
        # Update document status
        document.status = ProcessingStatus.BOOKED
        document.yuki_document_id = document_id
        document.yuki_booking_id = booking_id
        db.commit()
        
        return {
            "document_id": document.id,
            "status": "booked",
            "yuki_document_id": document_id,
            "yuki_booking_id": booking_id
        }
        
    except Exception as e:
        document.status = ProcessingStatus.ERROR
        document.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all documents with their processing status.
    """
    documents = db.query(Document).offset(skip).limit(limit).all()
    return documents

@router.get("/{document_id}")
async def get_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Get document details including extracted data and processing status.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document 