"""
FORMGUARD AI - Cross-Document Validation Engine
Deterministic rule-based verification across documents.
Works independently of any LLM.
"""

from typing import Dict, List, Optional
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.text_normalizer import (
    normalize_name, normalize_date, normalize_academic_year,
    compute_text_similarity, extract_amount, normalize_text,
    is_initials_match,
)


class ValidationEngine:
    """
    Deterministic cross-document validation engine.
    Compares extracted fields across documents and applies scheme rules.
    """

    def __init__(
        self,
        scheme_id: str,
        scheme_data: Dict,
        academic_year: str,
        applicant_category: str = "",
        name_match_threshold: float = 0.85,
    ):
        self.scheme_id = scheme_id
        self.scheme_data = scheme_data
        self.academic_year = academic_year
        self.applicant_category = applicant_category
        self.name_threshold = name_match_threshold

    def check_required_documents(self, extractions: Dict) -> List[Dict]:
        """Check if all required documents are present."""
        checks = []
        required = self.scheme_data.get("required_documents", [])

        for doc_type in required:
            if doc_type in extractions:
                extraction = extractions[doc_type]
                has_text = bool(extraction.get("raw_text", "").strip())
                has_fields = bool(extraction.get("extracted_fields"))

                if has_text and has_fields:
                    checks.append(self._make_check(
                        name=f"Document Present: {self._doc_name(doc_type)}",
                        severity="PASS",
                        field="document_presence",
                        sources=[doc_type],
                        result="Document uploaded and processed successfully.",
                        reason=f"{self._doc_name(doc_type)} is present and text was extracted.",
                        action="",
                    ))
                elif has_text and not has_fields:
                    checks.append(self._make_check(
                        name=f"Document Readable: {self._doc_name(doc_type)}",
                        severity="MANUAL_REVIEW",
                        field="document_readability",
                        sources=[doc_type],
                        result="Text extracted but no structured fields identified.",
                        reason="The document was readable but key fields could not be automatically identified.",
                        action="Please review the extracted text and manually verify the required information.",
                    ))
                else:
                    checks.append(self._make_check(
                        name=f"Document Readable: {self._doc_name(doc_type)}",
                        severity="WARNING",
                        field="document_readability",
                        sources=[doc_type],
                        result="No text could be extracted.",
                        reason="The document may be a scanned image with poor quality or an unsupported format.",
                        action="Re-upload a clearer scan or a text-based PDF.",
                    ))
            else:
                checks.append(self._make_check(
                    name=f"Missing Required Document: {self._doc_name(doc_type)}",
                    severity="CRITICAL",
                    field="document_presence",
                    sources=[doc_type],
                    result="Required document not uploaded.",
                    reason=f"{self._doc_name(doc_type)} is required for {self.scheme_data.get('name', 'this scheme')} but was not uploaded.",
                    action=f"Please upload your {self._doc_name(doc_type)}.",
                ))

        return checks

    def check_name_consistency(self, extractions: Dict) -> List[Dict]:
        """Check if the applicant name is consistent across all documents."""
        checks = []

        # Collect all name fields from all documents
        name_entries = []
        for doc_type, extraction in extractions.items():
            fields = extraction.get("extracted_fields", {})
            for field_name in ["applicant_name", "student_name", "account_holder_name", "name"]:
                if field_name in fields:
                    field_data = fields[field_name]
                    value = field_data.get("value", "") if isinstance(field_data, dict) else str(field_data)
                    if value.strip():
                        name_entries.append({
                            "doc_type": doc_type,
                            "field_name": field_name,
                            "original_value": value,
                            "normalized": normalize_name(value),
                        })

        if len(name_entries) < 2:
            if len(name_entries) == 1:
                checks.append(self._make_check(
                    name="Name Consistency",
                    severity="MANUAL_REVIEW",
                    field="applicant_name",
                    sources=[name_entries[0]["doc_type"]],
                    values={name_entries[0]["doc_type"]: name_entries[0]["original_value"]},
                    result="Name found in only one document.",
                    reason="Cannot cross-verify name as it was extracted from only one document.",
                    action="Ensure your name appears consistently across all certificates.",
                ))
            return checks

        # Compare all pairs
        reference = name_entries[0]
        all_match = True
        mismatch_details = []

        for other in name_entries[1:]:
            similarity = compute_text_similarity(reference["normalized"], other["normalized"])
            initials_matched = is_initials_match(reference["original_value"], other["original_value"])

            if similarity >= self.name_threshold:
                # Names match
                pass
            elif initials_matched:
                # Initials detected (e.g. R. S. Patil vs Rahul Suresh Patil)
                all_match = False
                mismatch_details.append({
                    "doc1": reference["doc_type"],
                    "doc2": other["doc_type"],
                    "name1": reference["original_value"],
                    "name2": other["original_value"],
                    "similarity": similarity,
                    "is_initials": True,
                })
            elif similarity >= 0.6:
                # Partial match - possible variant
                all_match = False
                mismatch_details.append({
                    "doc1": reference["doc_type"],
                    "doc2": other["doc_type"],
                    "name1": reference["original_value"],
                    "name2": other["original_value"],
                    "similarity": similarity,
                    "is_initials": False,
                })
            else:
                # Significant mismatch
                all_match = False
                mismatch_details.append({
                    "doc1": reference["doc_type"],
                    "doc2": other["doc_type"],
                    "name1": reference["original_value"],
                    "name2": other["original_value"],
                    "similarity": similarity,
                    "is_initials": False,
                })

        if all_match:
            values = {e["doc_type"]: e["original_value"] for e in name_entries}
            checks.append(self._make_check(
                name="Name Consistency",
                severity="PASS",
                field="applicant_name",
                sources=[e["doc_type"] for e in name_entries],
                values=values,
                result="Name matches across all documents.",
                reason="The applicant name is consistent across all uploaded documents.",
                action="",
            ))
        else:
            for mismatch in mismatch_details:
                if mismatch.get("is_initials"):
                    severity = "WARNING"
                    reason = (
                        f"Initials detected in {self._doc_name(mismatch['doc2'])} ('{mismatch['name2']}') "
                        f"versus full name in {self._doc_name(mismatch['doc1'])} ('{mismatch['name1']}')."
                    )
                    action = (
                        "MahaDBT scholarship guidelines recommend that bank accounts and certificates bear the exact "
                        "full name as per Aadhaar. Verify if your college nodal desk accepts initials or update your "
                        "bank passbook to match official identity documents to avoid DBT disbursement failure."
                    )
                else:
                    severity = "WARNING" if mismatch["similarity"] >= 0.6 else "CRITICAL"
                    reason = (
                        f"Name in {self._doc_name(mismatch['doc1'])} ('{mismatch['name1']}') "
                        f"differs from {self._doc_name(mismatch['doc2'])} ('{mismatch['name2']}')."
                    )
                    action = (
                        "Ensure your name is spelled exactly the same on all certificates. If there is a genuine "
                        "difference, you may need to get the document re-issued or provide a name correction affidavit."
                    )

                checks.append(self._make_check(
                    name=f"Name Mismatch: {self._doc_name(mismatch['doc1'])} vs {self._doc_name(mismatch['doc2'])}",
                    severity=severity,
                    field="applicant_name",
                    sources=[mismatch["doc1"], mismatch["doc2"]],
                    values={
                        mismatch["doc1"]: mismatch["name1"],
                        mismatch["doc2"]: mismatch["name2"],
                    },
                    result=f"Name mismatch (similarity: {mismatch['similarity']:.0%})",
                    reason=reason,
                    action=action,
                ))

        return checks

    def check_date_consistency(self, extractions: Dict) -> List[Dict]:
        """Check dates and academic year consistency."""
        checks = []

        # Check academic year matches selected year
        for doc_type, extraction in extractions.items():
            fields = extraction.get("extracted_fields", {})

            # Check academic year field
            for year_field in ["academic_year", "year"]:
                if year_field in fields:
                    field_data = fields[year_field]
                    value = field_data.get("value", "") if isinstance(field_data, dict) else str(field_data)
                    normalized = normalize_academic_year(value)

                    if normalized and self.academic_year:
                        expected = normalize_academic_year(self.academic_year)
                        
                        # Special domain handling for marksheet (qualifying exam is previous year)
                        if doc_type == "marksheet":
                            try:
                                m_start = int(normalized.split("-")[0])
                                e_start = int(expected.split("-")[0])
                                # Previous 1-3 years is acceptable for previous marksheet
                                if 0 <= (e_start - m_start) <= 3:
                                    checks.append(self._make_check(
                                        name=f"Academic Year Qualifying: {self._doc_name(doc_type)}",
                                        severity="PASS",
                                        field="academic_year",
                                        sources=[doc_type],
                                        values={doc_type: value, "application_year": self.academic_year},
                                        result=f"Previous examination year ({value}) valid for application session {self.academic_year}.",
                                        reason=f"Previous academic session marksheet ({value}) is valid qualifying record for {self.academic_year}.",
                                        action="",
                                    ))
                                    continue
                            except Exception:
                                pass

                        if normalized == expected:
                            checks.append(self._make_check(
                                name=f"Academic Year Match: {self._doc_name(doc_type)}",
                                severity="PASS",
                                field="academic_year",
                                sources=[doc_type],
                                values={doc_type: value, "selected": self.academic_year},
                                result="Academic year matches.",
                                reason=f"Academic year in {self._doc_name(doc_type)} matches the selected year.",
                                action="",
                            ))
                        else:
                            checks.append(self._make_check(
                                name=f"Academic Year Mismatch: {self._doc_name(doc_type)}",
                                severity="WARNING",
                                field="academic_year",
                                sources=[doc_type],
                                values={doc_type: value, "selected": self.academic_year},
                                result=f"Academic year mismatch: '{value}' vs selected '{self.academic_year}'.",
                                reason=f"The academic year in {self._doc_name(doc_type)} ('{value}') does not match your selected year ('{self.academic_year}').",
                                action="Verify that you are uploading documents for the correct academic year. If this is a previous year's document, ensure it is acceptable for your application.",
                            ))

            # Validate issue dates are not in the future
            for date_field in ["issue_date"]:
                if date_field in fields:
                    field_data = fields[date_field]
                    value = field_data.get("value", "") if isinstance(field_data, dict) else str(field_data)
                    if value:
                        checks.append(self._make_check(
                            name=f"Date Present: {self._doc_name(doc_type)}",
                            severity="PASS",
                            field="issue_date",
                            sources=[doc_type],
                            values={doc_type: value},
                            result="Issue date found.",
                            reason=f"Issue date ({value}) found in {self._doc_name(doc_type)}.",
                            action="",
                        ))

        return checks

    def check_missing_fields(self, extractions: Dict) -> List[Dict]:
        """Check for missing expected fields in each document."""
        checks = []

        # Import document type expected fields
        from config import DOCUMENT_TYPES

        for doc_type, extraction in extractions.items():
            doc_config = DOCUMENT_TYPES.get(doc_type, {})
            expected_fields = doc_config.get("expected_fields", [])
            extracted_fields = extraction.get("extracted_fields", {})

            if not expected_fields:
                continue

            missing_fields = []
            found_fields = []

            for field in expected_fields:
                if field in extracted_fields:
                    field_data = extracted_fields[field]
                    value = field_data.get("value", "") if isinstance(field_data, dict) else str(field_data)
                    if value.strip():
                        found_fields.append(field)
                    else:
                        missing_fields.append(field)
                else:
                    missing_fields.append(field)

            if missing_fields:
                # Determine severity based on how critical the missing fields are
                critical_fields = {"applicant_name", "student_name", "certificate_number", "account_number"}
                has_critical = any(f in critical_fields for f in missing_fields)

                checks.append(self._make_check(
                    name=f"Missing Fields: {self._doc_name(doc_type)}",
                    severity="MANUAL_REVIEW" if not has_critical else "WARNING",
                    field="expected_fields",
                    sources=[doc_type],
                    values={"missing": ", ".join(f.replace("_", " ").title() for f in missing_fields)},
                    result=f"{len(missing_fields)} expected field(s) not extracted.",
                    reason=f"Could not extract: {', '.join(f.replace('_', ' ').title() for f in missing_fields)}. "
                           f"This may be due to OCR limitations or document format.",
                    action="Review the extracted text to verify if these fields are present. "
                           "You may need to correct them manually.",
                ))
            else:
                checks.append(self._make_check(
                    name=f"All Fields Present: {self._doc_name(doc_type)}",
                    severity="PASS",
                    field="expected_fields",
                    sources=[doc_type],
                    result=f"All {len(found_fields)} expected fields extracted.",
                    reason=f"All expected fields were found in {self._doc_name(doc_type)}.",
                    action="",
                ))

        return checks

    def check_scheme_requirements(self, extractions: Dict) -> List[Dict]:
        """Check scheme-specific requirements."""
        checks = []

        # Income limit check
        income_limit = self.scheme_data.get("income_limit")
        if income_limit and "income_certificate" in extractions:
            fields = extractions["income_certificate"].get("extracted_fields", {})
            income_field = fields.get("annual_income", {})
            income_value = income_field.get("value", "") if isinstance(income_field, dict) else str(income_field)

            if income_value:
                amount = extract_amount(income_value)
                if amount is not None:
                    if amount <= income_limit:
                        checks.append(self._make_check(
                            name="Income Eligibility Check",
                            severity="PASS",
                            field="annual_income",
                            sources=["income_certificate"],
                            values={
                                "income_certificate": income_value,
                                "scheme_limit": f"₹{income_limit:,.0f}",
                            },
                            result=f"Income (₹{amount:,.0f}) is within the scheme limit (₹{income_limit:,.0f}).",
                            reason="Extracted income appears to be within the scheme's income eligibility criteria.",
                            action="",
                        ))
                    else:
                        checks.append(self._make_check(
                            name="Income Eligibility Check",
                            severity="WARNING",
                            field="annual_income",
                            sources=["income_certificate"],
                            values={
                                "income_certificate": income_value,
                                "scheme_limit": f"₹{income_limit:,.0f}",
                            },
                            result=f"Income (₹{amount:,.0f}) may exceed scheme limit (₹{income_limit:,.0f}).",
                            reason=f"The extracted annual income (₹{amount:,.0f}) appears to exceed the scheme's income limit of ₹{income_limit:,.0f}. "
                                   "Note: OCR extraction may not be perfectly accurate.",
                            action="Verify your income certificate amount. If your family income exceeds the scheme limit, you may not be eligible for this particular scholarship.",
                        ))

        # Category match check
        if self.applicant_category and "caste_certificate" in extractions:
            fields = extractions["caste_certificate"].get("extracted_fields", {})
            category_field = fields.get("category", {})
            cert_category = category_field.get("value", "") if isinstance(category_field, dict) else str(category_field)

            if cert_category:
                if normalize_text(cert_category) == normalize_text(self.applicant_category):
                    checks.append(self._make_check(
                        name="Category Match",
                        severity="PASS",
                        field="category",
                        sources=["caste_certificate"],
                        values={
                            "caste_certificate": cert_category,
                            "selected_category": self.applicant_category,
                        },
                        result="Category matches.",
                        reason=f"Category in caste certificate ({cert_category}) matches your selected category ({self.applicant_category}).",
                        action="",
                    ))
                else:
                    checks.append(self._make_check(
                        name="Category Mismatch",
                        severity="WARNING",
                        field="category",
                        sources=["caste_certificate"],
                        values={
                            "caste_certificate": cert_category,
                            "selected_category": self.applicant_category,
                        },
                        result=f"Category mismatch: '{cert_category}' vs selected '{self.applicant_category}'.",
                        reason=f"The category in your caste certificate ({cert_category}) does not match your selected category ({self.applicant_category}).",
                        action="Ensure you have selected the correct category, or verify that your caste certificate reflects the right category.",
                    ))

        return checks

    def check_duplicate_documents(self, uploaded_documents: Dict) -> List[Dict]:
        """Check for duplicate document uploads."""
        checks = []
        hashes = {}

        for doc_type, doc_info in uploaded_documents.items():
            file_hash = doc_info.get("file_hash", "")
            if file_hash:
                if file_hash in hashes:
                    other_type = hashes[file_hash]
                    checks.append(self._make_check(
                        name=f"Duplicate Document: {self._doc_name(doc_type)}",
                        severity="WARNING",
                        field="duplicate_check",
                        sources=[doc_type, other_type],
                        result="Same file uploaded for two different document types.",
                        reason=f"The file uploaded as {self._doc_name(doc_type)} is identical to the file uploaded as {self._doc_name(other_type)}.",
                        action="Please upload the correct distinct document for each type.",
                    ))
                else:
                    hashes[file_hash] = doc_type

        return checks

    # ── Helper Methods ──

    def _doc_name(self, doc_type: str) -> str:
        """Get display name for a document type."""
        from config import DOCUMENT_TYPES
        return DOCUMENT_TYPES.get(doc_type, {}).get("display_name", doc_type.replace("_", " ").title())

    def _make_check(
        self,
        name: str,
        severity: str,
        field: str,
        sources: List[str] = None,
        values: Dict = None,
        result: str = "",
        reason: str = "",
        action: str = "",
    ) -> Dict:
        """Create a standardized verification check result."""
        return {
            "check_name": name,
            "severity": severity,
            "field_checked": field,
            "document_sources": sources or [],
            "extracted_values": values or {},
            "comparison_result": result,
            "reason": reason,
            "recommended_action": action,
            "is_ai_generated": False,
        }
