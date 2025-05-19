from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum
from datetime import datetime

Base = declarative_base()

class ProcessingStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    EXTRACTED = "extracted"
    VALIDATED = "validated"
    UPLOADED = "uploaded"
    BOOKED = "booked"
    ERROR = "error"

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Processing status
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    error_message = Column(String, nullable=True)
    
    # Extracted data
    extracted_data = Column(JSON, nullable=True)
    confidence_scores = Column(JSON, nullable=True)
    
    # Yuki integration
    yuki_document_id = Column(String, nullable=True)
    yuki_booking_id = Column(String, nullable=True)
    
    # Relationships
    validations = relationship("DocumentValidation", back_populates="document")
    audit_logs = relationship("AuditLog", back_populates="document")

class DocumentValidation(Base):
    __tablename__ = "document_validations"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    validated_by = Column(String, nullable=False)
    validated_at = Column(DateTime, default=datetime.utcnow)
    validation_data = Column(JSON, nullable=False)
    notes = Column(String, nullable=True)
    
    # Relationship
    document = relationship("Document", back_populates="validations")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    action = Column(String, nullable=False)
    performed_by = Column(String, nullable=False)
    performed_at = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON, nullable=True)
    
    # Relationship
    document = relationship("Document", back_populates="audit_logs")

class YukiAdministration(Base):
    __tablename__ = "yuki_administrations"
    
    id = Column(Integer, primary_key=True, index=True)
    administration_id = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # API credentials
    api_username = Column(String, nullable=False)
    api_password = Column(String, nullable=False)
    api_url = Column(String, nullable=False) 