"""
FORMGUARD AI - End-to-End Integration Test
Exercises the full pipeline: synthetic PDFs → OCR → field extraction →
cross-document validation → RAG evidence → PDF report generation.

Test scenarios:
  A) Name mismatch between income cert and bank document
  B) Missing domicile certificate (required)
  C) Academic-year inconsistency on college bonafide
"""

import sys, os, io, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# ── Step 0: Generate synthetic PDF documents using ReportLab ─────────────────

def create_pdf(text_lines: list[str]) -> bytes:
    """Create a simple PDF from lines of text. Returns raw bytes."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    elements = []
    for line in text_lines:
        elements.append(Paragraph(line, styles["Normal"]))
        elements.append(Spacer(1, 6))
    doc.build(elements)
    return buf.getvalue()


INCOME_CERT_TEXT = [
    "GOVERNMENT OF MAHARASHTRA",
    "OFFICE OF THE TAHSILDAR, PUNE CITY",
    "",
    "INCOME CERTIFICATE",
    "",
    "Certificate No: INC/2026/MH/00321",
    "Date: 12/04/2026",
    "",
    "This is to certify that:",
    "",
    "Name of Applicant: Rahul Suresh Patil",
    "Son of: Shri Suresh Ramchandra Patil",
    "Address: 42 Shivaji Nagar, Pune 411005, Maharashtra",
    "",
    "The annual income of the family from all sources is:",
    "Rs. 1,80,000/- (Rupees One Lakh Eighty Thousand Only)",
    "",
    "Financial Year: 2025-2026",
    "Issuing Authority: Tahsildar, Pune City",
    "Place: Pune",
]

CASTE_CERT_TEXT = [
    "GOVERNMENT OF MAHARASHTRA",
    "OFFICE OF THE SUB-DIVISIONAL OFFICER, PUNE",
    "",
    "CASTE CERTIFICATE",
    "",
    "Certificate No: CST/2026/MH/00147",
    "Date: 05/03/2026",
    "",
    "This is to certify that:",
    "",
    "Name: Rahul Suresh Patil",
    "Son of: Shri Suresh Ramchandra Patil",
    "Resident of: 42 Shivaji Nagar, Pune, Maharashtra",
    "",
    "Belongs to the OBC category.",
    "Caste: Kunbi",
    "Sub-Caste: Leva Patil",
    "",
    "Issuing Authority: Sub-Divisional Officer, Pune",
]

# ── Intentional name mismatch: "R. S. Patil" vs "Rahul Suresh Patil"
BANK_DOC_TEXT = [
    "STATE BANK OF INDIA",
    "Pune Main Branch",
    "",
    "BANK PASSBOOK - FIRST PAGE",
    "",
    "Account Holder Name: R. S. Patil",
    "Account No: 39aborting876543210",
    "A/C No: 9876543210123",
    "IFSC Code: SBIN0001234",
    "Branch: Pune Main Branch",
    "",
    "Date of Opening: 10/01/2020",
]

# ── Intentional academic-year inconsistency: says 2024-2025 instead of 2026-2027
BONAFIDE_TEXT = [
    "ABC COLLEGE OF ENGINEERING, PUNE",
    "(Affiliated to Savitribai Phule Pune University)",
    "",
    "BONAFIDE CERTIFICATE",
    "",
    "Student Name: Rahul Suresh Patil",
    "Enrollment Number: EN2026001",
    "Course: B.E. Computer Science and Engineering",
    "Academic Year: 2024-2025",
    "Year of Study: Third Year (T.E.)",
    "",
    "is a bonafide student of this institution.",
    "",
    "Date: 15/07/2026",
    "Principal, ABC College of Engineering, Pune",
]

MARKSHEET_TEXT = [
    "SAVITRIBAI PHULE PUNE UNIVERSITY",
    "",
    "STATEMENT OF MARKS",
    "",
    "Examination: Second Year B.E. (2024-2025)",
    "Student Name: Rahul Suresh Patil",
    "Seat Number: T19CS042",
    "College: ABC College of Engineering, Pune",
    "",
    "Total Marks: 485/650",
    "Percentage: 74.6%",
    "Result: PASSED",
    "",
    "Year: 2024-2025",
]

# ── NOTE: domicile_certificate is intentionally NOT created (missing document test)

# =============================================================================
# Main integration test
# =============================================================================

def run_integration_test():
    from modules.ocr_engine import extract_text_from_file
    from modules.field_extractor import extract_fields_from_text
    from modules.validation_engine import ValidationEngine
    from modules.rag_pipeline import RAGPipeline
    from modules.ai_explainer import AIExplainer
    from modules.risk_analyzer import RiskAnalyzer
    from modules.report_generator import ReportGenerator
    from modules.security import validate_file
    from config import SUPPORTED_SCHEMES, DOCUMENT_TYPES, TEMP_DIR

    print("=" * 72)
    print("  FORMGUARD AI — End-to-End Integration Test")
    print("=" * 72)

    # ── 1. Create synthetic PDFs ──────────────────────────────────────────
    print("\n▶ STEP 1: Creating synthetic PDF documents …")
    docs = {
        "income_certificate":  ("income_cert.pdf",  INCOME_CERT_TEXT),
        "caste_certificate":   ("caste_cert.pdf",   CASTE_CERT_TEXT),
        "bank_document":       ("bank_doc.pdf",     BANK_DOC_TEXT),
        "college_bonafide":    ("bonafide.pdf",     BONAFIDE_TEXT),
        "marksheet":           ("marksheet.pdf",    MARKSHEET_TEXT),
        # domicile_certificate → deliberately missing
    }

    os.makedirs(str(TEMP_DIR), exist_ok=True)
    saved_paths: dict[str, dict] = {}

    for doc_type, (filename, lines) in docs.items():
        pdf_bytes = create_pdf(lines)
        # security validation
        ok, msg = validate_file(pdf_bytes, filename)
        assert ok, f"Security validation failed for {filename}: {msg}"
        path = os.path.join(str(TEMP_DIR), f"integ_{filename}")
        with open(path, "wb") as f:
            f.write(pdf_bytes)
        saved_paths[doc_type] = {
            "file_name": filename,
            "file_path": path,
            "file_size": len(pdf_bytes),
            "file_hash": __import__('hashlib').sha256(pdf_bytes).hexdigest(),
            "mime_type": "application/pdf",
            "document_type": doc_type,
        }
        print(f"  ✔ {filename:25s}  ({len(pdf_bytes):,} bytes)  [{doc_type}]")

    print(f"\n  ⚠ domicile_certificate  — deliberately NOT created (missing-doc test)")

    # ── 2. OCR / text extraction ──────────────────────────────────────────
    print("\n▶ STEP 2: Running OCR / text extraction …")
    raw_texts: dict[str, str] = {}
    for doc_type, info in saved_paths.items():
        text, confidence, warnings = extract_text_from_file(info["file_path"])
        raw_texts[doc_type] = text
        snippet = text[:120].replace("\n", " ") if text else "(empty)"
        print(f"  {doc_type:25s}  conf={confidence:.0%}  len={len(text):>5}  "
              f"snippet=\"{snippet}…\"")
        for w in warnings:
            print(f"    ⚠ {w}")

    # ── 3. Structured field extraction ────────────────────────────────────
    print("\n▶ STEP 3: Extracting structured fields …")
    extractions: dict = {}
    for doc_type, info in saved_paths.items():
        text = raw_texts[doc_type]
        fields, field_warnings = extract_fields_from_text(text, doc_type)
        extractions[doc_type] = {
            "document_type": doc_type,
            "file_name": info["file_name"],
            "raw_text": text,
            "extracted_fields": fields,
            "extraction_confidence": 0.75,
            "warnings": field_warnings,
            "errors": [],
        }
        print(f"\n  📄 {DOCUMENT_TYPES.get(doc_type,{}).get('display_name', doc_type)}")
        if fields:
            for fname, fdata in fields.items():
                val = fdata.get("value","") if isinstance(fdata, dict) else fdata
                conf = fdata.get("confidence",0) if isinstance(fdata, dict) else 0
                print(f"     {fname:28s} = {str(val):40s}  (conf {conf:.0%})")
        else:
            print("     (no fields extracted)")
        for w in field_warnings:
            print(f"     ⚠ {w}")

    # ── 4. Cross-document validation ──────────────────────────────────────
    print("\n▶ STEP 4: Running cross-document verification …")
    scheme_id = "mahadbt_postmatric"
    scheme_data = SUPPORTED_SCHEMES[scheme_id]
    academic_year = "2026-2027"       # the year the student selected
    category = "OBC"

    engine = ValidationEngine(
        scheme_id=scheme_id,
        scheme_data=scheme_data,
        academic_year=academic_year,
        applicant_category=category,
    )

    all_checks = []
    t0 = time.time()

    checks_presence   = engine.check_required_documents(extractions)
    checks_name       = engine.check_name_consistency(extractions)
    checks_date       = engine.check_date_consistency(extractions)
    checks_fields     = engine.check_missing_fields(extractions)
    checks_scheme     = engine.check_scheme_requirements(extractions)
    checks_duplicates = engine.check_duplicate_documents(saved_paths)

    all_checks = (checks_presence + checks_name + checks_date +
                  checks_fields + checks_scheme + checks_duplicates)
    elapsed = time.time() - t0

    # Classify and print
    pass_ct = sum(1 for c in all_checks if c["severity"] == "PASS")
    warn_ct = sum(1 for c in all_checks if c["severity"] == "WARNING")
    crit_ct = sum(1 for c in all_checks if c["severity"] == "CRITICAL")
    rev_ct  = sum(1 for c in all_checks if c["severity"] == "MANUAL_REVIEW")

    print(f"\n  Results ({elapsed:.2f}s):  "
          f"✅ {pass_ct} PASS  |  ⚠️ {warn_ct} WARNING  |  "
          f"❌ {crit_ct} CRITICAL  |  🔍 {rev_ct} MANUAL_REVIEW")
    print(f"  Total checks: {len(all_checks)}")

    sev_order = {"CRITICAL": 0, "WARNING": 1, "MANUAL_REVIEW": 2, "PASS": 3}
    for c in sorted(all_checks, key=lambda x: sev_order.get(x["severity"], 9)):
        icon = {"CRITICAL":"❌","WARNING":"⚠️","MANUAL_REVIEW":"🔍","PASS":"✅"}.get(c["severity"],"?")
        print(f"\n  {icon} [{c['severity']:14s}] {c['check_name']}")
        print(f"    Field:  {c['field_checked']}")
        if c.get("extracted_values"):
            for k, v in c["extracted_values"].items():
                label = DOCUMENT_TYPES.get(k,{}).get("display_name", k)
                print(f"    Value:  {label} → \"{v}\"")
        print(f"    Reason: {c['reason']}")
        if c.get("recommended_action"):
            print(f"    Action: {c['recommended_action']}")

    # ── 5. Readiness score ────────────────────────────────────────────────
    readiness = RiskAnalyzer.compute_readiness_score(all_checks)
    summary = RiskAnalyzer.generate_summary(all_checks)
    print(f"\n▶ STEP 5: Readiness score = {readiness:.1f}%")
    print(f"  Status: {summary['status']}")
    print(f"  Recommendation: {summary['recommendation']}")

    # ── 6. RAG evidence retrieval ─────────────────────────────────────────
    print("\n▶ STEP 6: RAG evidence retrieval …")
    rag = RAGPipeline()

    queries = [
        "name mismatch across documents scholarship",
        "missing domicile certificate requirement",
        "academic year inconsistency bonafide",
        "income eligibility limit OBC post matric",
    ]
    for q in queries:
        results = rag.query(q, scheme_id=scheme_id, top_k=2)
        print(f"\n  🔎 Query: \"{q}\"")
        for i, r in enumerate(results):
            score = r.get("relevance_score", 0)
            print(f"     [{i+1}] (score {score:.2f}) {r.get('title','')}")
            print(f"         {r['text'][:150]}…")
            print(f"         Source: {r.get('source','')} — {r.get('source_url','')}")

    # ── 7. AI explanation (template mode) ─────────────────────────────────
    print("\n▶ STEP 7: AI explanations (template fallback) …")
    explainer = AIExplainer()

    # Explain the most critical issues
    critical_checks = [c for c in all_checks if c["severity"] in ("CRITICAL","WARNING")]
    for c in critical_checks[:3]:
        explanation = explainer.explain_check(c, language="en")
        print(f"\n  💡 Issue: {c['check_name']}")
        print(f"     Explanation: {explanation.get('explanation','')[:200]}")
        if explanation.get("recommended_steps"):
            for step in explanation["recommended_steps"][:3]:
                print(f"     → {step}")
        if explanation.get("sources"):
            print(f"     Sources: {explanation['sources'][:2]}")

    # ── 8. PDF report generation ──────────────────────────────────────────
    print("\n▶ STEP 8: Generating PDF report …")
    generator = ReportGenerator()

    verification_result = {
        "session_id": "INTEG-TEST-001",
        "scheme_id": scheme_id,
        "scheme_name": scheme_data["name"],
        "academic_year": academic_year,
        "applicant_category": category,
        "documents_processed": len(extractions),
        "checks": all_checks,
        "pass_count": pass_ct,
        "warning_count": warn_ct,
        "critical_count": crit_ct,
        "manual_review_count": rev_ct,
        "overall_readiness": readiness,
    }

    pdf_bytes = generator.generate_report(
        verification_id="FG-INTEG-20261121",
        verification_result=verification_result,
        extractions=extractions,
    )

    if pdf_bytes:
        report_path = os.path.join(str(TEMP_DIR), "integration_test_report.pdf")
        with open(report_path, "wb") as f:
            f.write(pdf_bytes)
        print(f"  ✔ PDF report generated: {len(pdf_bytes):,} bytes")
        print(f"    Saved to: {report_path}")
        assert pdf_bytes[:5] == b'%PDF-', "Output is not a valid PDF"
    else:
        print("  ✖ PDF generation failed!")

    # ── 9. Assertions ─────────────────────────────────────────────────────
    print("\n▶ STEP 9: Verifying expected outcomes …")
    errors = []

    # A) Name mismatch should be detected
    name_issues = [c for c in all_checks
                   if "name" in c["check_name"].lower()
                   and c["severity"] in ("WARNING", "CRITICAL")]
    if name_issues:
        print(f"  ✅ Name mismatch detected ({len(name_issues)} issue(s))")
    else:
        errors.append("Name mismatch NOT detected between income cert and bank doc")
        print(f"  ❌ Name mismatch NOT detected!")

    # B) Missing domicile certificate → CRITICAL
    missing_issues = [c for c in all_checks
                      if "missing" in c["check_name"].lower()
                      and "domicile" in c["check_name"].lower()
                      and c["severity"] == "CRITICAL"]
    if missing_issues:
        print(f"  ✅ Missing domicile certificate flagged as CRITICAL")
    else:
        errors.append("Missing domicile certificate NOT flagged as CRITICAL")
        print(f"  ❌ Missing domicile certificate NOT flagged!")

    # C) Academic year mismatch
    year_issues = [c for c in all_checks
                   if "academic" in c["check_name"].lower()
                   and c["severity"] in ("WARNING", "CRITICAL")]
    if year_issues:
        print(f"  ✅ Academic year inconsistency detected ({len(year_issues)} issue(s))")
    else:
        errors.append("Academic year inconsistency NOT detected")
        print(f"  ❌ Academic year inconsistency NOT detected!")

    # D) Income should PASS (180k < 250k limit)
    income_pass = [c for c in all_checks
                   if "income" in c["check_name"].lower()
                   and c["severity"] == "PASS"]
    if income_pass:
        print(f"  ✅ Income within limit correctly identified as PASS")
    else:
        # Check if income was even checked
        income_any = [c for c in all_checks if "income" in c["check_name"].lower()]
        if income_any:
            print(f"  ⚠️  Income check found but not PASS: {income_any[0]['severity']}")
        else:
            print(f"  ⚠️  No income eligibility check was run")

    # E) RAG should return relevant results
    rag_test = rag.query("required documents scholarship application", scheme_id=scheme_id)
    if rag_test:
        print(f"  ✅ RAG returns relevant results ({len(rag_test)} chunks)")
    else:
        errors.append("RAG returned no results")
        print(f"  ❌ RAG returned no results!")

    # F) PDF report should be valid
    if pdf_bytes and pdf_bytes[:5] == b'%PDF-':
        print(f"  ✅ PDF report is valid ({len(pdf_bytes):,} bytes)")
    else:
        errors.append("PDF report invalid or not generated")

    # ── Final verdict ─────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    if errors:
        print(f"  ❌ INTEGRATION TEST FAILED — {len(errors)} issue(s):")
        for e in errors:
            print(f"     • {e}")
    else:
        print("  ✅ INTEGRATION TEST PASSED — All scenarios verified!")
    print("=" * 72)

    return errors


if __name__ == "__main__":
    failures = run_integration_test()
    sys.exit(1 if failures else 0)
