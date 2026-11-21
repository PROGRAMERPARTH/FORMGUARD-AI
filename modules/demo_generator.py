"""
FORMGUARD AI - Demo Document Generator
Generates synthetic government application documents for instant demo and evaluation.
"""

import os
import io
import hashlib
from typing import Dict
from pathlib import Path


def create_demo_pdf(text_lines: list[str]) -> bytes:
    """Create a standardized synthetic PDF from text lines using ReportLab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    
    style_header = ParagraphStyle(
        'GovHeader',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=HexColor('#1B2A4A'),
        spaceAfter=4,
    )
    style_normal = ParagraphStyle(
        'GovBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=HexColor('#1E293B'),
    )

    elements = []
    for line in text_lines:
        if not line.strip():
            elements.append(Spacer(1, 8))
        elif any(kw in line for kw in ["GOVERNMENT", "CERTIFICATE", "UNIVERSITY", "STATEMENT", "STATE BANK", "COLLEGE"]):
            elements.append(Paragraph(f"<b>{line}</b>", style_header))
        else:
            elements.append(Paragraph(line, style_normal))
        elements.append(Spacer(1, 4))

    doc.build(elements)
    return buf.getvalue()


DEMO_DOCUMENTS = {
    "income_certificate": {
        "filename": "demo_income_certificate.pdf",
        "lines": [
            "GOVERNMENT OF MAHARASHTRA",
            "OFFICE OF THE TAHSILDAR, PUNE CITY",
            "",
            "INCOME CERTIFICATE (उत्पन्न दाखला)",
            "Certificate No: INC/2026/MH/00321",
            "Issue Date: 12/04/2026",
            "",
            "This is to certify that:",
            "Name of Applicant: Rahul Suresh Patil",
            "Son of: Shri Suresh Ramchandra Patil",
            "Address: 42 Shivaji Nagar, Pune 411005, Maharashtra",
            "",
            "The annual income of the family from all sources is:",
            "Rs. 1,80,000/- (Rupees One Lakh Eighty Thousand Only)",
            "Financial Year: 2025-2026",
            "",
            "Issuing Authority: Tahsildar, Pune City",
            "Place: Pune",
        ],
    },
    "caste_certificate": {
        "filename": "demo_caste_certificate.pdf",
        "lines": [
            "GOVERNMENT OF MAHARASHTRA",
            "OFFICE OF THE SUB-DIVISIONAL OFFICER, PUNE",
            "",
            "CASTE CERTIFICATE (जात प्रमाणपत्र)",
            "Certificate No: CST/2026/MH/00147",
            "Issue Date: 05/03/2026",
            "",
            "This is to certify that:",
            "Name: Rahul Suresh Patil",
            "Son of: Shri Suresh Ramchandra Patil",
            "Resident of: 42 Shivaji Nagar, Pune, Maharashtra",
            "",
            "Belongs to the OBC category.",
            "Caste: Kunbi",
            "Sub-Caste: Leva Patil",
            "",
            "Issuing Authority: Sub-Divisional Officer, Pune",
        ],
    },
    "bank_document": {
        "filename": "demo_bank_passbook.pdf",
        "lines": [
            "STATE BANK OF INDIA",
            "Pune Main Branch",
            "",
            "SAVINGS ACCOUNT PASSBOOK - FIRST PAGE",
            "Account Holder Name: R. S. Patil",
            "Account No: 9876543210123",
            "IFSC Code: SBIN0001234",
            "Branch: Pune Main Branch",
            "Account Status: Active",
            "Date: 10/01/2020",
        ],
    },
    "college_bonafide": {
        "filename": "demo_bonafide_certificate.pdf",
        "lines": [
            "ABC COLLEGE OF ENGINEERING, PUNE",
            "(Affiliated to Savitribai Phule Pune University)",
            "",
            "BONAFIDE / ENROLLMENT CERTIFICATE",
            "Student Name: Rahul Suresh Patil",
            "Enrollment Number: EN2026001",
            "Course: B.E. Computer Science and Engineering",
            "Academic Year: 2024-2025",
            "Year of Study: Third Year (T.E.)",
            "",
            "This is to certify that the above mentioned student is a bonafide student of this institution.",
            "Issue Date: 15/07/2026",
            "Principal, ABC College of Engineering, Pune",
        ],
    },
    "marksheet": {
        "filename": "demo_marksheet.pdf",
        "lines": [
            "SAVITRIBAI PHULE PUNE UNIVERSITY",
            "ABC College of Engineering, Pune",
            "",
            "STATEMENT OF MARKS (Second Year B.E.)",
            "Student Name: Rahul Suresh Patil",
            "Seat Number: T19CS042",
            "Examination: Second Year B.E. (Computer Engineering)",
            "Year: 2024-2025",
            "Total Marks: 485/650",
            "Percentage: 74.6%",
            "Result: PASSED",
        ],
    },
}


def generate_all_demo_documents(target_dir: str) -> Dict[str, Dict]:
    """
    Generates all demo synthetic documents and saves them to target_dir.
    Returns a dictionary structured for st.session_state.uploaded_documents.
    """
    os.makedirs(target_dir, exist_ok=True)
    uploaded_docs = {}

    for doc_type, data in DEMO_DOCUMENTS.items():
        pdf_bytes = create_demo_pdf(data["lines"])
        file_path = os.path.join(target_dir, data["filename"])
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)
            
        file_hash = hashlib.sha256(pdf_bytes).hexdigest()
        uploaded_docs[doc_type] = {
            "file_name": data["filename"],
            "file_path": file_path,
            "file_size": len(pdf_bytes),
            "file_hash": file_hash,
            "mime_type": "application/pdf",
            "document_type": doc_type,
            "is_duplicate": False,
        }

    return uploaded_docs
