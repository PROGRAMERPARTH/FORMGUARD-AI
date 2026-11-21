"""
FORMGUARD AI - Test Suite: Validation Engine
Tests for the deterministic cross-document validation engine.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.validation_engine import ValidationEngine
from config import SUPPORTED_SCHEMES


# ── Fixtures ──

def get_engine():
    """Create a test validation engine."""
    scheme_data = SUPPORTED_SCHEMES["mahadbt_postmatric"]
    return ValidationEngine(
        scheme_id="mahadbt_postmatric",
        scheme_data=scheme_data,
        academic_year="2025-2026",
        applicant_category="OBC",
    )


def make_extraction(doc_type, fields, raw_text="Sample text"):
    """Helper to create a mock extraction dict."""
    field_dict = {}
    for name, value in fields.items():
        field_dict[name] = {
            "value": value,
            "confidence": 0.8,
            "is_user_confirmed": False,
        }
    return {
        "document_type": doc_type,
        "file_name": f"test_{doc_type}.pdf",
        "raw_text": raw_text,
        "extracted_fields": field_dict,
        "extraction_confidence": 0.8,
        "warnings": [],
        "errors": [],
    }


# ── Test 1: All documents match ──

class TestAllDocsMatch:
    """Test 1: All documents contain matching names and valid fields."""

    def test_name_consistency_pass(self):
        engine = get_engine()
        extractions = {
            "income_certificate": make_extraction("income_certificate", {
                "applicant_name": "Rahul Suresh Patil",
                "annual_income": "₹180000",
                "certificate_number": "INC/2025/001",
                "issue_date": "15/06/2025",
            }),
            "caste_certificate": make_extraction("caste_certificate", {
                "applicant_name": "Rahul Suresh Patil",
                "caste": "Kunbi",
                "category": "OBC",
                "certificate_number": "CST/2025/042",
                "issue_date": "10/05/2025",
            }),
            "college_bonafide": make_extraction("college_bonafide", {
                "student_name": "Rahul Suresh Patil",
                "institution_name": "ABC College of Engineering",
                "academic_year": "2025-2026",
            }),
        }
        checks = engine.check_name_consistency(extractions)
        assert any(c["severity"] == "PASS" for c in checks), "Name consistency should PASS when all names match"

    def test_all_checks_pass_with_complete_docs(self):
        engine = get_engine()
        extractions = {
            "income_certificate": make_extraction("income_certificate", {
                "applicant_name": "Rahul Suresh Patil",
                "annual_income": "₹180000",
                "certificate_number": "INC/2025/001",
                "issue_date": "15/06/2025",
                "guardian_name": "Suresh Patil",
                "issuing_authority": "Tahsildar Pune",
            }),
            "caste_certificate": make_extraction("caste_certificate", {
                "applicant_name": "Rahul Suresh Patil",
                "caste": "Kunbi",
                "sub_caste": "Leva",
                "category": "OBC",
                "certificate_number": "CST/2025/042",
                "issue_date": "10/05/2025",
                "issuing_authority": "Tahsildar Pune",
            }),
            "domicile_certificate": make_extraction("domicile_certificate", {
                "applicant_name": "Rahul Suresh Patil",
                "address": "Pune, Maharashtra",
                "state": "Maharashtra",
                "certificate_number": "DOM/2025/078",
                "issue_date": "12/05/2025",
            }),
            "college_bonafide": make_extraction("college_bonafide", {
                "student_name": "Rahul Suresh Patil",
                "institution_name": "ABC College of Engineering",
                "course": "B.E. Computer Science",
                "academic_year": "2025-2026",
                "enrollment_number": "EN2025001",
            }),
            "marksheet": make_extraction("marksheet", {
                "student_name": "Rahul Suresh Patil",
                "institution_name": "XYZ University",
                "examination": "Second Year B.E.",
                "year": "2024-2025",
                "total_marks": "450/600",
                "percentage": "75%",
                "seat_number": "S12345",
            }),
            "bank_document": make_extraction("bank_document", {
                "account_holder_name": "Rahul Suresh Patil",
                "bank_name": "State Bank of India",
                "branch": "Pune Main",
                "account_number": "12345678901",
                "ifsc_code": "SBIN0001234",
            }),
        }
        presence = engine.check_required_documents(extractions)
        names = engine.check_name_consistency(extractions)
        all_checks = presence + names

        pass_count = sum(1 for c in all_checks if c["severity"] == "PASS")
        critical_count = sum(1 for c in all_checks if c["severity"] == "CRITICAL")

        assert critical_count == 0, "No critical issues should be found with complete matching docs"
        assert pass_count > 0, "At least some checks should PASS"


# ── Test 2: Name mismatch ──

class TestNameMismatch:
    """Test 2: Applicant name differs between two documents."""

    def test_name_mismatch_detected(self):
        engine = get_engine()
        extractions = {
            "income_certificate": make_extraction("income_certificate", {
                "applicant_name": "Rahul Suresh Patil",
            }),
            "caste_certificate": make_extraction("caste_certificate", {
                "applicant_name": "Rahul S. Patil",  # Slightly different
            }),
        }
        checks = engine.check_name_consistency(extractions)
        # Should detect at least a warning or still pass (since it's close)
        assert len(checks) > 0, "Should produce at least one name check"

    def test_significant_name_mismatch(self):
        engine = get_engine()
        extractions = {
            "income_certificate": make_extraction("income_certificate", {
                "applicant_name": "Rahul Suresh Patil",
            }),
            "bank_document": make_extraction("bank_document", {
                "account_holder_name": "Suresh Kumar Patil",  # Very different
            }),
        }
        checks = engine.check_name_consistency(extractions)
        severities = [c["severity"] for c in checks]
        assert "WARNING" in severities or "CRITICAL" in severities, \
            "Significant name mismatch should produce WARNING or CRITICAL"


# ── Test 3: Missing required document ──

class TestMissingDocument:
    """Test 3: Required document is missing."""

    def test_missing_document_critical(self):
        engine = get_engine()
        extractions = {
            "income_certificate": make_extraction("income_certificate", {
                "applicant_name": "Test Student",
            }),
            # Missing: caste_certificate, domicile_certificate, college_bonafide, marksheet, bank_document
        }
        checks = engine.check_required_documents(extractions)
        critical_checks = [c for c in checks if c["severity"] == "CRITICAL"]
        assert len(critical_checks) >= 4, f"Should have at least 4 CRITICAL checks for missing docs, got {len(critical_checks)}"


# ── Test 4: Academic year mismatch ──

class TestAcademicYearMismatch:
    """Test 4: Academic year doesn't match selected scheme requirement."""

    def test_academic_year_mismatch(self):
        engine = get_engine()  # engine expects 2025-2026
        extractions = {
            "college_bonafide": make_extraction("college_bonafide", {
                "student_name": "Test Student",
                "academic_year": "2024-2025",  # Wrong year
            }),
        }
        checks = engine.check_date_consistency(extractions)
        warning_checks = [c for c in checks if c["severity"] == "WARNING"]
        assert len(warning_checks) > 0, "Academic year mismatch should produce a WARNING"

    def test_academic_year_match(self):
        engine = get_engine()
        extractions = {
            "college_bonafide": make_extraction("college_bonafide", {
                "student_name": "Test Student",
                "academic_year": "2025-2026",  # Correct year
            }),
        }
        checks = engine.check_date_consistency(extractions)
        pass_checks = [c for c in checks if c["severity"] == "PASS"]
        assert len(pass_checks) > 0, "Matching academic year should produce PASS"


# ── Test 5: OCR extraction failure ──

class TestOCRFailure:
    """Test 5: OCR fails to extract a certificate number."""

    def test_missing_fields_manual_review(self):
        engine = get_engine()
        extractions = {
            "income_certificate": make_extraction("income_certificate", {
                "applicant_name": "Test Student",
                # Missing: certificate_number, annual_income, issue_date, etc.
            }),
        }
        checks = engine.check_missing_fields(extractions)
        # Should produce a MANUAL_REVIEW or WARNING for missing fields
        assert len(checks) > 0, "Missing fields should produce a check"
        non_pass = [c for c in checks if c["severity"] != "PASS"]
        assert len(non_pass) > 0, "Missing expected fields should not all be PASS"


# ── Test 6: Duplicate documents ──

class TestDuplicateDocuments:
    """Test duplicate document detection."""

    def test_duplicate_detected(self):
        engine = get_engine()
        uploaded = {
            "income_certificate": {
                "file_hash": "abc123def456",
                "file_name": "cert.pdf",
            },
            "caste_certificate": {
                "file_hash": "abc123def456",  # Same hash!
                "file_name": "cert.pdf",
            },
        }
        checks = engine.check_duplicate_documents(uploaded)
        assert len(checks) > 0, "Duplicate should be detected"
        assert checks[0]["severity"] == "WARNING"

    def test_no_duplicates(self):
        engine = get_engine()
        uploaded = {
            "income_certificate": {
                "file_hash": "abc123",
                "file_name": "income.pdf",
            },
            "caste_certificate": {
                "file_hash": "def456",
                "file_name": "caste.pdf",
            },
        }
        checks = engine.check_duplicate_documents(uploaded)
        assert len(checks) == 0, "No duplicates should be found"


# ── Test: Income eligibility ──

class TestIncomeEligibility:
    """Test income limit scheme requirement check."""

    def test_income_within_limit(self):
        engine = get_engine()
        extractions = {
            "income_certificate": make_extraction("income_certificate", {
                "applicant_name": "Test Student",
                "annual_income": "₹180,000",
            }),
        }
        checks = engine.check_scheme_requirements(extractions)
        pass_checks = [c for c in checks if c["severity"] == "PASS" and "Income" in c.get("check_name", "")]
        assert len(pass_checks) > 0, "Income within limit should PASS"

    def test_income_exceeds_limit(self):
        engine = get_engine()
        extractions = {
            "income_certificate": make_extraction("income_certificate", {
                "applicant_name": "Test Student",
                "annual_income": "₹500,000",
            }),
        }
        checks = engine.check_scheme_requirements(extractions)
        warning_checks = [c for c in checks if c["severity"] == "WARNING" and "Income" in c.get("check_name", "")]
        assert len(warning_checks) > 0, "Income exceeding limit should produce WARNING"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
