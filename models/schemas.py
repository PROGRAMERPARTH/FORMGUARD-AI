"""
FORMGUARD AI - Pydantic Data Models
Structured schemas for documents, verification results, and reports.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class SeverityLevel(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class DocumentType(str, Enum):
    INCOME_CERTIFICATE = "income_certificate"
    CASTE_CERTIFICATE = "caste_certificate"
    DOMICILE_CERTIFICATE = "domicile_certificate"
    COLLEGE_BONAFIDE = "college_bonafide"
    MARKSHEET = "marksheet"
    BANK_DOCUMENT = "bank_document"
    AADHAAR_CARD = "aadhaar_card"
    OTHER = "other"


class SupportedLanguage(str, Enum):
    ENGLISH = "en"
    HINDI = "hi"
    MARATHI = "mr"


class ExtractedField(BaseModel):
    """A single field extracted from a document."""
    field_name: str
    value: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source_document: str = ""
    page_number: int = 1
    is_user_confirmed: bool = False
    original_value: Optional[str] = None


class DocumentUpload(BaseModel):
    """Represents an uploaded document."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_type: DocumentType
    file_name: str
    file_path: str
    file_size: int = 0
    mime_type: str = ""
    upload_timestamp: datetime = Field(default_factory=datetime.now)
    is_processed: bool = False


class DocumentExtraction(BaseModel):
    """Results of OCR and field extraction for a single document."""
    document_id: str
    document_type: DocumentType
    file_name: str
    raw_text: str = ""
    extracted_fields: List[ExtractedField] = []
    extraction_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    processing_time_seconds: float = 0.0
    ocr_engine_used: str = "tesseract"
    errors: List[str] = []
    warnings: List[str] = []


class VerificationCheck(BaseModel):
    """A single verification check result."""
    check_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    check_name: str
    check_description: str = ""
    severity: SeverityLevel
    field_checked: str
    document_sources: List[str] = []
    extracted_values: Dict[str, str] = {}
    comparison_result: str = ""
    reason: str = ""
    recommended_action: str = ""
    is_ai_generated: bool = False


class VerificationResult(BaseModel):
    """Complete verification result for a session."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scheme_id: str
    scheme_name: str
    academic_year: str
    applicant_category: str = ""
    documents_processed: int = 0
    verification_timestamp: datetime = Field(default_factory=datetime.now)
    checks: List[VerificationCheck] = []
    pass_count: int = 0
    warning_count: int = 0
    critical_count: int = 0
    manual_review_count: int = 0
    overall_readiness: float = Field(default=0.0, ge=0.0, le=100.0)
    processing_time_seconds: float = 0.0

    def compute_counts(self):
        self.pass_count = sum(1 for c in self.checks if c.severity == SeverityLevel.PASS)
        self.warning_count = sum(1 for c in self.checks if c.severity == SeverityLevel.WARNING)
        self.critical_count = sum(1 for c in self.checks if c.severity == SeverityLevel.CRITICAL)
        self.manual_review_count = sum(1 for c in self.checks if c.severity == SeverityLevel.MANUAL_REVIEW)
        total = len(self.checks)
        if total > 0:
            self.overall_readiness = round((self.pass_count / total) * 100, 1)


class RAGChunk(BaseModel):
    """A chunk of text from a government document."""
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    source_document: str
    source_url: str = ""
    scheme_name: str = ""
    page_number: int = 0
    section_title: str = ""
    metadata: Dict[str, Any] = {}


class RAGQueryResult(BaseModel):
    """Result from a RAG query."""
    query: str
    retrieved_chunks: List[RAGChunk] = []
    generated_explanation: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    sources_cited: List[str] = []
    language: SupportedLanguage = SupportedLanguage.ENGLISH


class VerificationReport(BaseModel):
    """Complete verification report for PDF generation."""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    verification_result: VerificationResult
    document_extractions: List[DocumentExtraction] = []
    rag_explanations: List[RAGQueryResult] = []
    generated_at: datetime = Field(default_factory=datetime.now)
    language: SupportedLanguage = SupportedLanguage.ENGLISH
    disclaimer: str = ""


class VerificationSession(BaseModel):
    """Tracks a complete verification session."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scheme_id: str = ""
    scheme_name: str = ""
    academic_year: str = ""
    applicant_category: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: str = "created"
    uploaded_documents: List[DocumentUpload] = []
    extractions: List[DocumentExtraction] = []
    verification_result: Optional[VerificationResult] = None
    report: Optional[VerificationReport] = None


class AssistantMessage(BaseModel):
    """A message in the AI assistant conversation."""
    role: str
    content: str
    language: SupportedLanguage = SupportedLanguage.ENGLISH
    timestamp: datetime = Field(default_factory=datetime.now)
    sources: List[str] = []
    is_grounded: bool = False
