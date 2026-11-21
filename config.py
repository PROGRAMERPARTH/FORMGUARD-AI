"""
FORMGUARD AI - Configuration Module
Centralized configuration management with environment variable support.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ── Base Paths ──
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
SCHEME_GUIDELINES_DIR = DATA_DIR / "scheme_guidelines"
SAMPLE_DOCUMENTS_DIR = DATA_DIR / "sample_documents"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"
ASSETS_DIR = BASE_DIR / "assets"
TEMP_DIR = BASE_DIR / "temp_uploads"

# Ensure directories exist
for d in [DATA_DIR, SCHEME_GUIDELINES_DIR, SAMPLE_DOCUMENTS_DIR, VECTOR_STORE_DIR, TEMP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── API Keys ──
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ── Application Settings ──
APP_NAME = "FORMGUARD AI"
APP_TAGLINE = "Detect Before You Submit."
APP_VERSION = "1.0.0"
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# ── File Upload Settings ──
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", "pdf,jpg,jpeg,png").split(",")
ALLOWED_MIME_TYPES = {
    "pdf": "application/pdf",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
}

# ── OCR Settings ──
OCR_ENGINE = os.getenv("OCR_ENGINE", "tesseract")
TESSERACT_PATH = os.getenv("TESSERACT_PATH", "")

# ── RAG Settings ──
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

# ── Security Settings ──
MASK_AADHAAR = os.getenv("MASK_AADHAAR", "true").lower() == "true"
MASK_BANK_ACCOUNT = os.getenv("MASK_BANK_ACCOUNT", "true").lower() == "true"
AUTO_DELETE_UPLOADS = os.getenv("AUTO_DELETE_UPLOADS", "true").lower() == "true"
UPLOAD_RETENTION_MINUTES = int(os.getenv("UPLOAD_RETENTION_MINUTES", "60"))

# ── Language Settings ──
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "हिन्दी (Hindi)",
    "mr": "मराठी (Marathi)",
}

# ── Verification Settings ──
NAME_MATCH_THRESHOLD = 0.85
DATE_FORMAT = "%d/%m/%Y"
ACADEMIC_YEAR_PATTERN = r"\d{4}-\d{4}"

# ── Severity Levels ──
class Severity:
    PASS = "PASS"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    MANUAL_REVIEW = "MANUAL_REVIEW"

# ── Supported Schemes ──
SUPPORTED_SCHEMES = {
    "mahadbt_postmatric": {
        "name": "MahaDBT Post-Matric Scholarship",
        "description": "Post-Matric scholarship for students belonging to SC/ST/OBC/VJNT/SBC categories in Maharashtra",
        "academic_years": ["2024-2025", "2025-2026", "2026-2027"],
        "categories": ["SC", "ST", "OBC", "VJNT", "SBC", "General (EWS)"],
        "required_documents": [
            "income_certificate",
            "caste_certificate",
            "domicile_certificate",
            "college_bonafide",
            "marksheet",
            "bank_document",
        ],
        "optional_documents": [
            "aadhaar_card",
        ],
        "income_limit": 250000,
        "source_url": "https://mahadbt.maharashtra.gov.in/",
        "faq_url": "https://mahadbt.maharashtra.gov.in/home/faq",
    }
}

# ── Document Type Mapping ──
DOCUMENT_TYPES = {
    "income_certificate": {
        "display_name": "Income Certificate",
        "expected_fields": ["applicant_name", "guardian_name", "annual_income", "issue_date", "certificate_number", "issuing_authority"],
        "file_label": "Income Certificate (Utpanna Dakhla)",
    },
    "caste_certificate": {
        "display_name": "Caste Certificate",
        "expected_fields": ["applicant_name", "caste", "sub_caste", "issue_date", "certificate_number", "issuing_authority"],
        "file_label": "Caste Certificate (Jaat Pramanpatra)",
    },
    "domicile_certificate": {
        "display_name": "Domicile Certificate",
        "expected_fields": ["applicant_name", "address", "state", "issue_date", "certificate_number"],
        "file_label": "Domicile Certificate (Abhivas Pramanpatra)",
    },
    "college_bonafide": {
        "display_name": "College Bonafide Certificate",
        "expected_fields": ["student_name", "institution_name", "course", "academic_year", "enrollment_number"],
        "file_label": "College Bonafide / Enrollment Certificate",
    },
    "marksheet": {
        "display_name": "Academic Marksheet",
        "expected_fields": ["student_name", "institution_name", "examination", "year", "total_marks", "percentage", "seat_number"],
        "file_label": "Previous Year Marksheet / Grade Card",
    },
    "bank_document": {
        "display_name": "Bank Passbook / Cancelled Cheque",
        "expected_fields": ["account_holder_name", "bank_name", "branch", "account_number", "ifsc_code"],
        "file_label": "Bank Passbook First Page / Cancelled Cheque",
    },
    "aadhaar_card": {
        "display_name": "Aadhaar Card",
        "expected_fields": ["name", "aadhaar_number", "address", "date_of_birth"],
        "file_label": "Aadhaar Card (UID)",
    },
}

# ── UI Theme ──
THEME = {
    "primary": "#1B2A4A",
    "secondary": "#2E5090",
    "accent": "#10B981",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "success": "#10B981",
    "background": "#F8FAFC",
    "card_bg": "#FFFFFF",
    "text_primary": "#1E293B",
    "text_secondary": "#64748B",
    "border": "#E2E8F0",
}

# ── Privacy Disclaimer ──
DISCLAIMER = (
    "This report provides AI-assisted document consistency and scheme-requirement checks. "
    "It is not an official government verification, eligibility decision, or guarantee of "
    "application approval. Always verify with official government portals and authorities."
)
