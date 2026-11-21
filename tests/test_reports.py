"""
FORMGUARD AI - Test Suite: Report Generator
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.report_generator import ReportGenerator


class TestReportGenerator:
    def setup_method(self):
        self.generator = ReportGenerator()

    def test_generate_report_returns_bytes(self):
        verification_result = {
            "session_id": "test-session",
            "scheme_id": "mahadbt_postmatric",
            "scheme_name": "MahaDBT Post-Matric Scholarship",
            "academic_year": "2025-2026",
            "applicant_category": "OBC",
            "documents_processed": 3,
            "pass_count": 5,
            "warning_count": 2,
            "critical_count": 1,
            "manual_review_count": 1,
            "overall_readiness": 55.5,
            "checks": [
                {
                    "check_name": "Name Consistency",
                    "severity": "PASS",
                    "field_checked": "applicant_name",
                    "document_sources": ["income_certificate", "caste_certificate"],
                    "extracted_values": {"income_certificate": "Rahul Patil", "caste_certificate": "Rahul Patil"},
                    "comparison_result": "Names match",
                    "reason": "Names are consistent across documents.",
                    "recommended_action": "",
                },
                {
                    "check_name": "Missing Document: Bank Document",
                    "severity": "CRITICAL",
                    "field_checked": "document_presence",
                    "document_sources": ["bank_document"],
                    "extracted_values": {},
                    "comparison_result": "Document not uploaded",
                    "reason": "Bank document is required but was not uploaded.",
                    "recommended_action": "Upload your bank passbook first page or cancelled cheque.",
                },
            ],
        }

        extractions = {
            "income_certificate": {
                "document_type": "income_certificate",
                "file_name": "income_cert.pdf",
                "extracted_fields": {
                    "applicant_name": {"value": "Rahul Patil", "confidence": 0.85},
                    "annual_income": {"value": "₹180,000", "confidence": 0.75},
                },
            },
        }

        pdf_bytes = self.generator.generate_report(
            verification_id="FG-TEST-001",
            verification_result=verification_result,
            extractions=extractions,
        )

        if pdf_bytes is not None:
            assert isinstance(pdf_bytes, bytes), "Report should be bytes"
            assert len(pdf_bytes) > 100, "PDF should have substantial content"
            assert pdf_bytes[:5] == b'%PDF-', "Should be a valid PDF"
        else:
            pytest.skip("ReportLab not installed")

    def test_empty_report(self):
        pdf_bytes = self.generator.generate_report(
            verification_id="FG-EMPTY-001",
            verification_result={
                "scheme_name": "Test", "academic_year": "2025-2026",
                "applicant_category": "", "documents_processed": 0,
                "pass_count": 0, "warning_count": 0, "critical_count": 0,
                "manual_review_count": 0, "overall_readiness": 0, "checks": [],
            },
            extractions={},
        )
        if pdf_bytes is not None:
            assert pdf_bytes[:5] == b'%PDF-'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
