"""
FORMGUARD AI - Text Normalization Utilities
Functions for cleaning and normalizing extracted text for comparison.
"""

import re
import unicodedata
from typing import Optional


def normalize_text(text: Optional[str]) -> str:
    """Basic text normalization for comparison."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.lower()
    return text


def normalize_name(name: Optional[str]) -> str:
    """Normalize a person's name for comparison."""
    if not name:
        return ""
    text = normalize_text(name)
    honorifics = [
        r"\bshri\.?\s*", r"\bsmt\.?\s*", r"\bkum\.?\s*",
        r"\bmr\.?\s*", r"\bmrs\.?\s*", r"\bms\.?\s*",
        r"\bdr\.?\s*", r"\bprof\.?\s*",
    ]
    for h in honorifics:
        text = re.sub(h, "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(".", "").replace(",", "")
    return text.strip()


def normalize_number(text: Optional[str]) -> str:
    """Extract and normalize numeric content."""
    if not text:
        return ""
    return re.sub(r"[^\d.\-]", "", str(text))


def normalize_date(date_str: Optional[str]) -> Optional[str]:
    """Normalize date string to DD/MM/YYYY format."""
    if not date_str:
        return None
    date_str = date_str.strip()

    match = re.match(r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})", date_str)
    if match:
        day, month, year = match.groups()
        return f"{int(day):02d}/{int(month):02d}/{year}"

    match = re.match(r"(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})", date_str)
    if match:
        year, month, day = match.groups()
        return f"{int(day):02d}/{int(month):02d}/{year}"

    months = {
        "jan": "01", "january": "01", "feb": "02", "february": "02",
        "mar": "03", "march": "03", "apr": "04", "april": "04",
        "may": "05", "jun": "06", "june": "06", "jul": "07", "july": "07",
        "aug": "08", "august": "08", "sep": "09", "september": "09",
        "oct": "10", "october": "10", "nov": "11", "november": "11",
        "dec": "12", "december": "12",
    }
    match = re.match(r"(\d{1,2})\s+(\w+)\s+(\d{4})", date_str, re.IGNORECASE)
    if match:
        day, month_name, year = match.groups()
        month_num = months.get(month_name.lower())
        if month_num:
            return f"{int(day):02d}/{month_num}/{year}"

    return date_str


def normalize_academic_year(year_str: Optional[str]) -> Optional[str]:
    """Normalize academic year to YYYY-YYYY format."""
    if not year_str:
        return None
    match = re.search(r"(\d{4})\s*[-–]\s*(\d{2,4})", str(year_str))
    if match:
        start = match.group(1)
        end = match.group(2)
        if len(end) == 2:
            end = start[:2] + end
        return f"{start}-{end}"
    return None


def extract_amount(text: Optional[str]) -> Optional[float]:
    """Extract monetary amount from text."""
    if not text:
        return None
    cleaned = re.sub(r"[₹$,Rs.\s]", "", str(text), flags=re.IGNORECASE)
    match = re.search(r"(\d+(?:\.\d+)?)", cleaned)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    return None


def compute_text_similarity(text1: str, text2: str) -> float:
    """Compute similarity ratio between two strings."""
    try:
        from rapidfuzz import fuzz
        return fuzz.ratio(text1, text2) / 100.0
    except ImportError:
        # Fallback: simple word overlap
        if not text1 or not text2:
            return 0.0
        set1 = set(text1.lower().split())
        set2 = set(text2.lower().split())
        if not set1 or not set2:
            return 1.0 if text1.lower() == text2.lower() else 0.0
        intersection = set1 & set2
        return len(intersection) / max(len(set1), len(set2))


def is_initials_match(name1: str, name2: str) -> bool:
    """
    Check if one name is an initials-based variation of another.
    Example: 'R. S. Patil' and 'Rahul Suresh Patil'
    """
    n1 = normalize_name(name1)
    n2 = normalize_name(name2)
    
    words1 = [w for w in n1.split() if w]
    words2 = [w for w in n2.split() if w]
    
    if len(words1) < 2 or len(words2) < 2:
        return False
        
    # Order so the abbreviated name (shorter total length) is words1
    if sum(len(w) for w in words1) > sum(len(w) for w in words2):
        words1, words2 = words2, words1
        
    # Check if last word (surname) matches
    if words1[-1] != words2[-1]:
        return False
        
    # Check if first words in words1 are initials of words2
    initials_to_check = words1[:-1]
    targets = words2[:-1]
    
    if len(initials_to_check) > len(targets):
        return False
        
    for i, init in enumerate(initials_to_check):
        if len(init) == 1:
            if not targets[i].startswith(init):
                return False
        elif init != targets[i]:
            return False
            
    return True


def mask_aadhaar(aadhaar: str) -> str:
    """Mask Aadhaar number, showing only last 4 digits."""
    digits = re.sub(r"\D", "", aadhaar)
    if len(digits) == 12:
        return f"XXXX-XXXX-{digits[-4:]}"
    return "XXXX-XXXX-XXXX"


def mask_bank_account(account: str) -> str:
    """Mask bank account number, showing only last 4 digits."""
    digits = re.sub(r"\D", "", account)
    if len(digits) >= 4:
        return "X" * (len(digits) - 4) + digits[-4:]
    return "XXXX"
