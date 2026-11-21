# FORMGUARD AI - Sample Documents

This directory contains synthetic sample documents for testing and demonstration purposes.

**These are NOT real government documents.**

They are fabricated for testing the OCR extraction, field matching, and cross-document verification features.

## Sample Files

### Test Case 1: All Matching (Expected: PASS)
- `sample_income_certificate.txt` - Income certificate with consistent name
- `sample_caste_certificate.txt` - Caste certificate with matching name
- `sample_bonafide.txt` - College bonafide with matching name and correct year

### Test Case 2: Name Mismatch (Expected: WARNING/CRITICAL)
- Use income certificate with name "Rahul Suresh Patil"
- Use bank document with name "Suresh Kumar Patil"

### Test Case 3: Missing Document (Expected: CRITICAL)
- Upload only income and caste certificates (missing domicile, bonafide, marksheet, bank)

### Test Case 4: Academic Year Mismatch (Expected: WARNING)
- Upload bonafide with academic year 2024-2025 when applying for 2025-2026

## Important Note

For actual demonstration, create PDF or image versions of these sample documents.
The text versions are provided for unit testing the extraction logic.
