"""
FORMGUARD AI - Structured Field Extractor Module
Converts raw OCR text into structured field dictionaries using pattern matching.
"""

import re
from typing import Dict, List, Tuple, Optional


def extract_fields_from_text(raw_text: str, document_type: str) -> Tuple[Dict, List[str]]:
    """
    Extract structured fields from raw text based on document type.
    Returns: (fields_dict, warnings)

    fields_dict format:
    {
        "field_name": {
            "value": "extracted value",
            "confidence": 0.0-1.0,
            "is_user_confirmed": False,
        }
    }
    """
    if not raw_text or not raw_text.strip():
        return {}, ["No text available for field extraction."]

    warnings = []

    # Route to document-specific extractor
    extractors = {
        "income_certificate": _extract_income_certificate,
        "caste_certificate": _extract_caste_certificate,
        "domicile_certificate": _extract_domicile_certificate,
        "college_bonafide": _extract_college_bonafide,
        "marksheet": _extract_marksheet,
        "bank_document": _extract_bank_document,
        "aadhaar_card": _extract_aadhaar,
    }

    extractor = extractors.get(document_type, _extract_generic)
    fields, extract_warnings = extractor(raw_text)
    warnings.extend(extract_warnings)

    # Add common fields that may appear in any document
    common_fields, common_warnings = _extract_common_fields(raw_text, fields)
    # Merge without overwriting document-specific extractions
    for key, value in common_fields.items():
        if key not in fields:
            fields[key] = value
    warnings.extend(common_warnings)

    return fields, warnings


def _make_field(value: Optional[str], confidence: float = 0.6) -> Dict:
    """Create a standardized field dict."""
    return {
        "value": value.strip() if value else "",
        "confidence": confidence,
        "is_user_confirmed": False,
    }


def _extract_common_fields(text: str, existing_fields: Dict) -> Tuple[Dict, List[str]]:
    """Extract fields common to many Indian government documents."""
    fields = {}
    warnings = []
    text_lower = text.lower()

    # Name extraction (try multiple patterns)
    if "applicant_name" not in existing_fields and "student_name" not in existing_fields:
        name = _find_name(text)
        if name:
            fields["applicant_name"] = _make_field(name, 0.5)
        else:
            warnings.append("Could not automatically detect applicant name.")

    # Date patterns
    dates = re.findall(r'\b(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})\b', text)
    if dates and "issue_date" not in existing_fields:
        fields["issue_date"] = _make_field(dates[0], 0.5)

    # Certificate number pattern
    cert_match = re.search(
        r'(?:certificate\s*(?:no|number|#)|cert\.?\s*no\.?|sr\.?\s*no\.?)[:\s]*([A-Z0-9/\-]+)',
        text, re.IGNORECASE
    )
    if cert_match and "certificate_number" not in existing_fields:
        fields["certificate_number"] = _make_field(cert_match.group(1), 0.6)

    return fields, warnings


def _find_name(text: str) -> Optional[str]:
    """Try to extract a person's name from text using multiple strategies."""
    # Priority 1: Direct explicit name labels
    explicit_patterns = [
        r'(?:name\s*(?:of\s*(?:the\s*)?)?(?:applicant|student|candidate|holder))[:\s]+([A-Za-z\s\.]+?)(?:\n|$)',
        r'(?:student|applicant|candidate|account\s*holder)\s*name[:\s]+([A-Za-z\s\.]+?)(?:\n|$)',
        r'(?:^|\n)\s*(?:name)[:\s]+([A-Za-z\s\.]+?)(?:\n|$)',
        r'(?:this\s+is\s+to\s+certify\s+that)\s+(?:shri|smt|kumari?|mr|mrs|ms)?\.?\s*([A-Za-z\s\.]+?)(?:\s+(?:is|has|son|daughter|s/o|d/o|w/o|\n|$))',
    ]

    for pattern in explicit_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            # Clean off any trailing comma or prefix honorific
            candidate = re.sub(r'^(?:shri|smt|kumari?|mr|mrs|ms)\.?\s+', '', candidate, flags=re.IGNORECASE).strip()
            if candidate and not re.search(r'\d', candidate) and len(candidate.split()) <= 6:
                if candidate.lower() not in ["certificate", "of applicant", "applicant", "student"]:
                    return candidate

    # Priority 2: Honorific match ONLY if the line doesn't mention son/daughter/father/mother/guardian
    lines = text.split('\n')
    for line in lines:
        line_clean = line.strip()
        if re.search(r'(?:father|mother|guardian|parent|son\s+of|daughter\s+of|s/o|d/o|w/o)', line_clean, re.IGNORECASE):
            continue
        h_match = re.search(r'\b(?:shri|smt|kumari?|mr|mrs|ms)\.?\s+([A-Za-z\s\.]+?)(?:,|\n|$)', line_clean, re.IGNORECASE)
        if h_match:
            candidate = h_match.group(1).strip()
            if len(candidate.split()) >= 2 and not re.search(r'\d', candidate):
                return candidate

    return None


def _extract_income_certificate(text: str) -> Tuple[Dict, List[str]]:
    """Extract fields from an income certificate."""
    fields = {}
    warnings = []
    text_lower = text.lower()

    # Applicant name
    name = _find_name(text)
    if name:
        fields["applicant_name"] = _make_field(name, 0.65)

    # Guardian / parent name
    guardian_patterns = [
        r'(?:father|mother|guardian|parent)[\'s]*\s*name[:\s]+([A-Za-z\s\.]+?)(?:\n|$)',
        r'(?:s/o|d/o|w/o|son\s+of|daughter\s+of)[:\s]+([A-Za-z\s\.]+?)(?:\n|,|$)',
    ]
    for pattern in guardian_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            fields["guardian_name"] = _make_field(match.group(1), 0.6)
            break

    # Annual income
    income_patterns = [
        r'(?:annual\s+income|yearly\s+income|total\s+income|income)[:\s]*(?:rs\.?|₹)?\s*([\d,\.]+)',
        r'(?:rs\.?|₹)\s*([\d,\.]+)\s*(?:per\s*annum|annually|/\-)',
    ]
    for pattern in income_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            income_str = match.group(1).replace(',', '')
            fields["annual_income"] = _make_field(f"₹{income_str}", 0.65)
            break

    # Certificate number
    cert_match = re.search(r'(?:certificate|cert\.?)\s*(?:no|number|#)[:\s]*([A-Z0-9/\-]+)', text, re.IGNORECASE)
    if cert_match:
        fields["certificate_number"] = _make_field(cert_match.group(1), 0.7)

    # Issue date
    date_match = re.search(r'(?:date|dated|issue\s*date)[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})', text, re.IGNORECASE)
    if date_match:
        fields["issue_date"] = _make_field(date_match.group(1), 0.7)

    # Issuing authority
    authority_patterns = [
        r'(?:issued\s+by|issuing\s+authority|tahsildar|naib\s+tahsildar|collector)[:\s]+([A-Za-z\s\.,\-]+?)(?:\n|$)',
        r'(?:^|\n)\s*(tahsildar[A-Za-z\s\.,\-]+)(?:\n|$)',
    ]
    for pattern in authority_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            fields["issuing_authority"] = _make_field(match.group(1).strip(), 0.5)
            break

    return fields, warnings


def _extract_caste_certificate(text: str) -> Tuple[Dict, List[str]]:
    """Extract fields from a caste certificate."""
    fields = {}
    warnings = []

    # Name
    name = _find_name(text)
    if name:
        fields["applicant_name"] = _make_field(name, 0.65)

    # Caste
    caste_patterns = [
        r'\b(?:caste|jati|jaat)[:\s]+([A-Za-z\s]+?)(?:\n|,|\.|$)',
        r'(?:belongs?\s+to)\s+([A-Za-z\s]+?)(?:\s+(?:caste|community|category))',
    ]
    for pattern in caste_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            cval = match.group(1).strip()
            # Filter noise
            if cval.lower() not in ["certificate", "pramanpatra", "validity", "claim", "the obc", "the sc", "the st", "the"]:
                fields["caste"] = _make_field(cval, 0.65)
                break

    # Sub-caste
    sub_match = re.search(r'(?:sub[\-\s]?caste|upjati)[:\s]+([A-Za-z\s]+?)(?:\n|,|$)', text, re.IGNORECASE)
    if sub_match:
        fields["sub_caste"] = _make_field(sub_match.group(1), 0.6)

    # Category (SC/ST/OBC etc.)
    cat_match = re.search(r'\b(SC|ST|OBC|VJNT|SBC|NT|DT)\b', text)
    if cat_match:
        fields["category"] = _make_field(cat_match.group(1), 0.8)

    # Certificate number
    cert_match = re.search(r'(?:certificate|cert\.?)\s*(?:no|number|#)[:\s]*([A-Z0-9/\-]+)', text, re.IGNORECASE)
    if cert_match:
        fields["certificate_number"] = _make_field(cert_match.group(1), 0.7)

    # Issue date
    date_match = re.search(r'(?:date|dated)[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})', text, re.IGNORECASE)
    if date_match:
        fields["issue_date"] = _make_field(date_match.group(1), 0.7)

    # Issuing authority
    auth_match = re.search(r'(?:issued\s+by|issuing\s+authority|authority|tahsildar|sub[\-\s]?divisional\s+officer)[:\s]+([A-Za-z\s\.,\-]+?)(?:\n|$)', text, re.IGNORECASE)
    if auth_match:
        fields["issuing_authority"] = _make_field(auth_match.group(1).strip(), 0.5)

    return fields, warnings


def _extract_domicile_certificate(text: str) -> Tuple[Dict, List[str]]:
    """Extract fields from a domicile certificate."""
    fields = {}
    warnings = []

    name = _find_name(text)
    if name:
        fields["applicant_name"] = _make_field(name, 0.65)

    # Address
    addr_match = re.search(r'(?:address|resident\s+of|residing\s+at)[:\s]+(.+?)(?:\n\n|$)', text, re.IGNORECASE | re.DOTALL)
    if addr_match:
        address = addr_match.group(1).strip().replace('\n', ', ')[:200]
        fields["address"] = _make_field(address, 0.5)

    # State
    if re.search(r'maharashtra', text, re.IGNORECASE):
        fields["state"] = _make_field("Maharashtra", 0.9)

    # Certificate number
    cert_match = re.search(r'(?:certificate|cert\.?)\s*(?:no|number|#)[:\s]*([A-Z0-9/\-]+)', text, re.IGNORECASE)
    if cert_match:
        fields["certificate_number"] = _make_field(cert_match.group(1), 0.7)

    # Issue date
    date_match = re.search(r'(?:date|dated)[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})', text, re.IGNORECASE)
    if date_match:
        fields["issue_date"] = _make_field(date_match.group(1), 0.7)

    return fields, warnings


def _extract_college_bonafide(text: str) -> Tuple[Dict, List[str]]:
    """Extract fields from a college bonafide certificate."""
    fields = {}
    warnings = []

    name = _find_name(text)
    if name:
        fields["student_name"] = _make_field(name, 0.65)

    # Institution name
    inst_patterns = [
        r'(?:college|university|institute|institution)\s*name[:\s]+(.+?)(?:\n|$)',
        r'(?:^|\n)\s*([A-Za-z\s,\.\-&]+(?:college|university|institute|polytechnic|academy)[A-Za-z\s,\.\-&]*)(?:\n|$)',
        r'(?:college|university|institute|institution)[:\s]+(.+?)(?:\n|$)',
    ]
    for pattern in inst_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            cand = match.group(1).strip()[:100]
            if len(cand) > 3 and not cand.lower().startswith("certificate"):
                fields["institution_name"] = _make_field(cand, 0.6)
                break

    # Course
    course_match = re.search(r'(?:course|programme|program|degree|branch)[:\s]+(.+?)(?:\n|$)', text, re.IGNORECASE)
    if course_match:
        fields["course"] = _make_field(course_match.group(1).strip()[:100], 0.6)

    # Academic year
    year_match = re.search(r'(?:academic\s+year|session|year)[:\s]*(\d{4}\s*[-–]\s*\d{2,4})', text, re.IGNORECASE)
    if year_match:
        fields["academic_year"] = _make_field(year_match.group(1), 0.7)

    # Enrollment number
    enroll_match = re.search(r'(?:enrollment|enrolment|roll|prn|gr)\s*(?:no|number|#)?[:\s]*([A-Z0-9/\-]+)', text, re.IGNORECASE)
    if enroll_match:
        fields["enrollment_number"] = _make_field(enroll_match.group(1), 0.65)

    return fields, warnings


def _extract_marksheet(text: str) -> Tuple[Dict, List[str]]:
    """Extract fields from an academic marksheet."""
    fields = {}
    warnings = []

    name = _find_name(text)
    if name:
        fields["student_name"] = _make_field(name, 0.65)

    # Institution
    inst_patterns = [
        r'(?:college|institute|board)\s*name[:\s]+(.+?)(?:\n|$)',
        r'(?:college|institute|board)[:\s]+(.+?)(?:\n|$)',
        r'(?:^|\n)\s*([A-Za-z\s,\.\-&]+(?:university|board|college)[A-Za-z\s,\.\-&]*)(?:\n|$)',
    ]
    for pattern in inst_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            cand = match.group(1).strip()[:100]
            if "statement of marks" not in cand.lower():
                fields["institution_name"] = _make_field(cand, 0.6)
                break

    # Examination
    exam_match = re.search(r'(?:examination|exam)[:\s]+(.+?)(?:\n|$)', text, re.IGNORECASE)
    if exam_match:
        fields["examination"] = _make_field(exam_match.group(1).strip(), 0.6)

    # Year
    year_match = re.search(r'(?:year|session)[:\s]*(\d{4}(?:\s*[-–]\s*\d{2,4})?)', text, re.IGNORECASE)
    if year_match:
        fields["year"] = _make_field(year_match.group(1), 0.6)

    # Percentage / CGPA
    pct_match = re.search(r'(?:percentage|percent|%)[:\s]*(\d+\.?\d*)', text, re.IGNORECASE)
    if pct_match:
        fields["percentage"] = _make_field(f"{pct_match.group(1)}%", 0.65)
    else:
        cgpa_match = re.search(r'(?:cgpa|gpa|grade\s*point)[:\s]*(\d+\.?\d*)', text, re.IGNORECASE)
        if cgpa_match:
            fields["percentage"] = _make_field(f"CGPA: {cgpa_match.group(1)}", 0.6)

    # Total marks
    marks_match = re.search(r'(?:total\s*marks?|aggregate)[:\s]*(\d+)\s*/\s*(\d+)', text, re.IGNORECASE)
    if marks_match:
        fields["total_marks"] = _make_field(f"{marks_match.group(1)}/{marks_match.group(2)}", 0.65)

    # Seat number
    seat_match = re.search(r'(?:seat|roll|hall\s*ticket)\s*(?:no|number|#)?[:\s]*([A-Z0-9]+)', text, re.IGNORECASE)
    if seat_match:
        fields["seat_number"] = _make_field(seat_match.group(1), 0.65)

    return fields, warnings


def _extract_bank_document(text: str) -> Tuple[Dict, List[str]]:
    """Extract fields from a bank passbook or cancelled cheque."""
    fields = {}
    warnings = []

    # Account holder name
    ah_match = re.search(r'(?:account\s*holder\s*(?:name)?|a/c\s*holder\s*(?:name)?|holder\s*name)[:\s]+([A-Za-z\s\.]+?)(?:\n|$)', text, re.IGNORECASE)
    if ah_match:
        fields["account_holder_name"] = _make_field(ah_match.group(1).strip(), 0.7)
    else:
        name = _find_name(text)
        if name:
            fields["account_holder_name"] = _make_field(name, 0.6)

    # Bank name
    bank_patterns = [
        r'(state\s+bank\s+of\s+india|sbi|bank\s+of\s+maharashtra|hdfc\s+bank|icici\s+bank|axis\s+bank|'
        r'punjab\s+national\s+bank|pnb|canara\s+bank|union\s+bank|bank\s+of\s+baroda|'
        r'central\s+bank\s+of\s+india|indian\s+bank|indian\s+overseas\s+bank|'
        r'kotak\s+mahindra\s+bank|yes\s+bank|idbi\s+bank|'
        r'[a-z\s]+(?:bank|co-?op(?:erative)?))',
    ]
    for pattern in bank_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            fields["bank_name"] = _make_field(match.group(1).strip().title(), 0.7)
            break

    # Branch
    branch_match = re.search(r'\bbranch[:\s]+([A-Za-z0-9\s,\.\-]+?)(?:\n|$)', text, re.IGNORECASE)
    if branch_match and "passbook" not in branch_match.group(1).lower():
        fields["branch"] = _make_field(branch_match.group(1).strip()[:100], 0.6)
    else:
        br_line = re.search(r'([A-Za-z\s]+?\s+branch)\b', text, re.IGNORECASE)
        if br_line and "passbook" not in br_line.group(1).lower():
            fields["branch"] = _make_field(br_line.group(1).strip(), 0.6)

    # Account number (9-18 digits)
    acct_match = re.search(r'(?:a/?c|account)\s*(?:no|number|#)?[:\s]*(\d{9,18})', text, re.IGNORECASE)
    if acct_match:
        fields["account_number"] = _make_field(acct_match.group(1), 0.7)

    # IFSC Code
    ifsc_match = re.search(r'(?:ifsc|ifs)\s*(?:code)?[:\s]*([A-Z]{4}0[A-Z0-9]{6})', text, re.IGNORECASE)
    if ifsc_match:
        fields["ifsc_code"] = _make_field(ifsc_match.group(1).upper(), 0.85)
    else:
        # Try standalone IFSC pattern
        ifsc_standalone = re.search(r'\b([A-Z]{4}0[A-Z0-9]{6})\b', text)
        if ifsc_standalone:
            fields["ifsc_code"] = _make_field(ifsc_standalone.group(1), 0.7)

    return fields, warnings


def _extract_aadhaar(text: str) -> Tuple[Dict, List[str]]:
    """Extract fields from Aadhaar card."""
    fields = {}
    warnings = []

    # Name
    name = _find_name(text)
    if name:
        fields["name"] = _make_field(name, 0.6)

    # Aadhaar number (12 digits)
    aadhaar_match = re.search(r'(\d{4}\s?\d{4}\s?\d{4})', text)
    if aadhaar_match:
        fields["aadhaar_number"] = _make_field(aadhaar_match.group(1), 0.8)

    # Date of birth
    dob_match = re.search(r'(?:dob|date\s+of\s+birth|birth|d\.o\.b)[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})', text, re.IGNORECASE)
    if dob_match:
        fields["date_of_birth"] = _make_field(dob_match.group(1), 0.7)

    # Gender
    gender_match = re.search(r'\b(male|female|transgender)\b', text, re.IGNORECASE)
    if gender_match:
        fields["gender"] = _make_field(gender_match.group(1).capitalize(), 0.8)

    return fields, warnings


def _extract_generic(text: str) -> Tuple[Dict, List[str]]:
    """Generic field extraction for unrecognized document types."""
    fields = {}
    warnings = ["Using generic extraction. Some fields may be missed."]

    name = _find_name(text)
    if name:
        fields["applicant_name"] = _make_field(name, 0.4)

    # Dates
    dates = re.findall(r'\b(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})\b', text)
    if dates:
        fields["date_found"] = _make_field(dates[0], 0.4)

    # Numbers that look like certificate numbers
    cert_match = re.search(r'(?:no|number|#)[:\s]*([A-Z0-9/\-]{4,})', text, re.IGNORECASE)
    if cert_match:
        fields["reference_number"] = _make_field(cert_match.group(1), 0.4)

    return fields, warnings
