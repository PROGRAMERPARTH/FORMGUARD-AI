"""
FORMGUARD AI - Security Module
File validation, sensitive data masking, and security utilities.
"""

import os
import re
import hashlib
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime


MAGIC_BYTES = {
    b'%PDF': 'application/pdf',
    b'\xff\xd8\xff': 'image/jpeg',
    b'\x89PNG': 'image/png',
}

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


def validate_file(file_content: bytes, filename: str) -> Tuple[bool, str]:
    """Validate uploaded file for security. Returns (is_valid, message)."""
    if not filename:
        return False, "No filename provided."

    ext = Path(filename).suffix.lower().lstrip('.')
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type '.{ext}' is not allowed. Accepted: {', '.join(ALLOWED_EXTENSIONS)}"

    if len(file_content) > MAX_FILE_SIZE_BYTES:
        size_mb = len(file_content) / (1024 * 1024)
        return False, f"File size ({size_mb:.1f} MB) exceeds the {MAX_FILE_SIZE_BYTES // (1024*1024)} MB limit."

    if len(file_content) == 0:
        return False, "File is empty."

    detected_type = detect_mime_type(file_content)
    if detected_type is None:
        return False, "Could not verify file type. The file may be corrupted."

    expected_mimes = {
        'pdf': 'application/pdf',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
    }
    expected = expected_mimes.get(ext)
    if expected and detected_type != expected:
        return False, f"File content does not match its extension '.{ext}'. Possible security risk."

    return True, "File validation passed."


def detect_mime_type(content: bytes) -> Optional[str]:
    """Detect MIME type from magic bytes."""
    for magic, mime in MAGIC_BYTES.items():
        if content[:len(magic)] == magic:
            return mime
    return None


def mask_aadhaar_number(text: str) -> str:
    """Mask Aadhaar numbers in text."""
    pattern = r'\b(\d{4})[\s\-]?(\d{4})[\s\-]?(\d{4})\b'
    def replacer(match):
        return f"XXXX XXXX {match.group(3)}"
    return re.sub(pattern, replacer, text)


def mask_bank_account_number(text: str) -> str:
    """Mask bank account numbers in text."""
    pattern = r'\b(\d{9,18})\b'
    def replacer(match):
        num = match.group(1)
        if len(num) >= 4:
            return 'X' * (len(num) - 4) + num[-4:]
        return 'XXXX'
    return re.sub(pattern, replacer, text)


def mask_sensitive_fields(text: str, mask_aadhaar: bool = True, mask_bank: bool = True) -> str:
    """Apply all relevant masking to text."""
    if mask_aadhaar:
        text = mask_aadhaar_number(text)
    if mask_bank:
        text = mask_bank_account_number(text)
    return text


def compute_file_hash(content: bytes) -> str:
    """Generate SHA-256 hash for file integrity / duplicate detection."""
    return hashlib.sha256(content).hexdigest()


def sanitize_path(path: str) -> str:
    """Prevent path traversal attacks."""
    resolved = Path(path).resolve()
    if '..' in str(resolved):
        raise ValueError("Path traversal detected")
    return str(resolved)


def log_access(action: str, details: str = "", sensitive: bool = False):
    """Log an access event without sensitive data."""
    timestamp = datetime.now().isoformat()
    if sensitive:
        details = "[REDACTED]"
    print(f"[AUDIT] {timestamp} | {action} | {details}")
