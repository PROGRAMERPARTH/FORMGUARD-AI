"""
FORMGUARD AI - Utility Helpers
Common utility functions used across the application.
"""

import os
import re
import uuid
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple


def generate_session_id() -> str:
    """Generate a unique session identifier."""
    return str(uuid.uuid4())


def generate_verification_id() -> str:
    """Generate a formatted verification ID."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    short_uuid = str(uuid.uuid4())[:8].upper()
    return f"FG-{timestamp}-{short_uuid}"


def get_file_hash(file_content: bytes) -> str:
    """Generate SHA-256 hash of file content for duplicate detection."""
    return hashlib.sha256(file_content).hexdigest()


def get_file_extension(filename: str) -> str:
    """Get lowercase file extension without dot."""
    return Path(filename).suffix.lower().lstrip(".")


def validate_file_type(filename: str, allowed_extensions: list) -> bool:
    """Check if file extension is in allowed list."""
    ext = get_file_extension(filename)
    return ext in allowed_extensions


def validate_file_size(file_size: int, max_size_bytes: int) -> bool:
    """Check if file size is within limit."""
    return file_size <= max_size_bytes


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable form."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def save_temp_file(file_content: bytes, filename: str, temp_dir: str) -> str:
    """Save uploaded file to temporary directory. Returns the file path."""
    os.makedirs(temp_dir, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
    filepath = os.path.join(temp_dir, unique_name)
    with open(filepath, "wb") as f:
        f.write(file_content)
    return filepath


def cleanup_temp_files(temp_dir: str, max_age_minutes: int = 60) -> int:
    """Delete temporary files older than max_age_minutes. Returns count deleted."""
    deleted = 0
    if not os.path.exists(temp_dir):
        return deleted
    now = datetime.now().timestamp()
    for filename in os.listdir(temp_dir):
        filepath = os.path.join(temp_dir, filename)
        if os.path.isfile(filepath):
            file_age_minutes = (now - os.path.getmtime(filepath)) / 60
            if file_age_minutes > max_age_minutes:
                try:
                    os.remove(filepath)
                    deleted += 1
                except OSError:
                    pass
    return deleted


def format_datetime(dt: datetime, fmt: str = "%d %b %Y, %I:%M %p") -> str:
    """Format datetime for display."""
    return dt.strftime(fmt)


def parse_academic_year(year_str: str) -> Optional[Tuple[int, int]]:
    """Parse academic year string like '2024-2025' into (start, end) tuple."""
    match = re.match(r"(\d{4})-(\d{4})", year_str.strip())
    if match:
        start = int(match.group(1))
        end = int(match.group(2))
        if end == start + 1:
            return (start, end)
    return None


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def sanitize_filename(filename: str) -> str:
    """Remove potentially dangerous characters from filename."""
    name = re.sub(r'[^\w\-.]', '_', filename)
    name = name.replace('..', '_')
    return name
