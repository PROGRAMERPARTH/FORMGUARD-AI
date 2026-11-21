"""
FORMGUARD AI - Application Readiness Report Page
Generate and download PDF verification reports.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DOCUMENT_TYPES, DISCLAIMER
from modules.report_generator import ReportGenerator
from utils.helpers import generate_verification_id


def render_report():
    """Render the report generation and download page."""
    st.markdown("""
    <div class="formguard-header">
        <h1>📋 Application Readiness Report</h1>
        <div class="tagline">Comprehensive verification report with recommendations</div>
    </div>
    """, unsafe_allow_html=True)

    verification_result = st.session_state.get("verification_result")
    extractions = st.session_state.get("extractions", {})

    if not verification_result:
        st.warning("⚠️ No verification results available. Please run verification first.")
        if st.button("← Go to Verification"):
            st.session_state.current_page = "verification"
            st.rerun()
        return

    # ── Report Summary ──
    verification_id = generate_verification_id()
    scheme_name = verification_result.get("scheme_name", "Unknown")
    academic_year = verification_result.get("academic_year", "Unknown")
    category = verification_result.get("applicant_category", "")
    readiness = verification_result.get("overall_readiness", 0)
    checks = verification_result.get("checks", [])

    st.markdown(f"""
    <div class="info-card">
        <div style="display: flex; justify-content: space-between; align-items: start;">
            <div>
                <strong style="font-size: 1.1rem;">🛡️ FORMGUARD AI Verification Report</strong><br>
                <span style="color: var(--text-secondary); font-size: 0.85rem;">
                    Report ID: {verification_id}<br>
                    Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}
                </span>
            </div>
            <div style="text-align: right;">
                <span class="badge {'badge-pass' if readiness >= 80 else 'badge-warning' if readiness >= 50 else 'badge-critical'}">
                    {'READY' if readiness >= 80 else 'NEEDS ATTENTION' if readiness >= 50 else 'SIGNIFICANT ISSUES'}
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Report Details ──
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📋 Application Details")
        st.markdown(f"""
        | Field | Value |
        |-------|-------|
        | **Scheme** | {scheme_name} |
        | **Academic Year** | {academic_year} |
        | **Category** | {category or 'N/A'} |
        | **Documents Processed** | {verification_result.get('documents_processed', 0)} |
        | **Verification Date** | {datetime.now().strftime('%d %b %Y')} |
        """)

    with col2:
        st.markdown("#### 📊 Verification Summary")
        st.markdown(f"""
        | Check Type | Count |
        |------------|-------|
        | ✅ **Passed** | {verification_result.get('pass_count', 0)} |
        | ⚠️ **Warnings** | {verification_result.get('warning_count', 0)} |
        | ❌ **Critical** | {verification_result.get('critical_count', 0)} |
        | 🔍 **Manual Review** | {verification_result.get('manual_review_count', 0)} |
        | **Overall Readiness** | **{readiness:.0f}%** |
        """)

    st.markdown("---")

    # ── Extracted Fields Comparison ──
    st.markdown("#### 🔍 Extracted Field Comparison")

    if extractions:
        # Collect all names across documents for comparison display
        name_fields = {}
        for doc_type, extraction in extractions.items():
            doc_name = DOCUMENT_TYPES.get(doc_type, {}).get("display_name", doc_type)
            fields = extraction.get("extracted_fields", {})
            for field_name, field_data in fields.items():
                if isinstance(field_data, dict):
                    value = field_data.get("value", "N/A")
                    confidence = field_data.get("confidence", 0)
                else:
                    value = str(field_data)
                    confidence = 0.5

                if field_name not in name_fields:
                    name_fields[field_name] = []
                name_fields[field_name].append({
                    "document": doc_name,
                    "value": value,
                    "confidence": f"{confidence:.0%}",
                })

        for field_name, entries in name_fields.items():
            with st.expander(f"📌 {field_name.replace('_', ' ').title()} (found in {len(entries)} document(s))"):
                for entry in entries:
                    st.markdown(f"  - **{entry['document']}**: `{entry['value']}` (confidence: {entry['confidence']})")

    st.markdown("---")

    # ── Detailed Issues ──
    st.markdown("#### ⚠️ Detected Issues & Recommendations")

    issue_checks = [c for c in checks if c.get("severity") != "PASS"]
    if issue_checks:
        for i, check in enumerate(issue_checks, 1):
            severity = check.get("severity", "WARNING")
            icon = "🔴" if severity == "CRITICAL" else "🟡" if severity == "WARNING" else "🔵"

            st.markdown(f"""
            **{i}. {icon} {check.get('check_name', 'Issue')}** [{severity}]
            - **Reason:** {check.get('reason', 'N/A')}
            - **Recommended Action:** {check.get('recommended_action', 'Review and correct the document.')}
            """)
    else:
        st.success("✅ No issues detected. All checks passed.")

    st.markdown("---")

    # ── Final Checklist ──
    st.markdown("#### ✅ Final Checklist")

    for check in checks:
        severity = check.get("severity", "PASS")
        if severity == "PASS":
            st.markdown(f"- [x] ✅ {check.get('check_name', 'Check')}")
        elif severity == "CRITICAL":
            st.markdown(f"- [ ] ❌ {check.get('check_name', 'Check')} — *{check.get('reason', '')}*")
        elif severity == "WARNING":
            st.markdown(f"- [ ] ⚠️ {check.get('check_name', 'Check')} — *{check.get('reason', '')}*")
        else:
            st.markdown(f"- [ ] 🔍 {check.get('check_name', 'Check')} — *{check.get('reason', '')}*")

    # Disclaimer
    st.markdown("---")
    st.warning(f"⚠️ **Disclaimer:** {DISCLAIMER}")

    # ── PDF Download ──
    st.markdown("---")
    st.markdown("### 📥 Download Report")

    col_dl1, col_dl2, col_dl3 = st.columns([1, 2, 1])
    with col_dl2:
        # Check if already generated or button clicked
        if st.button("📄 Generate PDF Report", type="primary", use_container_width=True):
            with st.spinner("Generating PDF report..."):
                try:
                    generator = ReportGenerator()
                    pdf_bytes = generator.generate_report(
                        verification_id=verification_id,
                        verification_result=verification_result,
                        extractions=extractions,
                        language=st.session_state.get("language", "en"),
                    )

                    if pdf_bytes:
                        st.session_state.total_reports_generated = (
                            st.session_state.get("total_reports_generated", 0) + 1
                        )
                        st.session_state.generated_pdf_bytes = pdf_bytes
                        st.session_state.generated_pdf_filename = f"FormGuard_Report_{verification_id}.pdf"
                        st.success("✅ Report generated successfully!")
                    else:
                        st.error("Failed to generate PDF report.")
                except Exception as e:
                    st.error(f"Error generating report: {str(e)}")
                    st.info("You can still review the on-screen report above.")

        # Always show download button if PDF exists in state
        if st.session_state.get("generated_pdf_bytes"):
            st.download_button(
                label="⬇️ Download Verification Report PDF",
                data=st.session_state.generated_pdf_bytes,
                file_name=st.session_state.get("generated_pdf_filename", f"FormGuard_Report_{verification_id}.pdf"),
                mime="application/pdf",
                use_container_width=True,
            )

    # ── Navigation ──
    st.markdown("<br>", unsafe_allow_html=True)
    col_back, col_dashboard, col_new = st.columns(3)

    with col_back:
        if st.button("← Back to Verification", use_container_width=True):
            st.session_state.current_page = "verification"
            st.rerun()

    with col_dashboard:
        if st.button("📊 Go to Dashboard", use_container_width=True):
            st.session_state.current_page = "dashboard"
            st.rerun()

    with col_new:
        if st.button("🚀 New Verification", type="primary", use_container_width=True):
            # Reset for new session
            st.session_state.session_id = None
            st.session_state.uploaded_documents = {}
            st.session_state.extractions = {}
            st.session_state.verification_result = None
            st.session_state.chat_history = []
            st.session_state.current_page = "upload"
            st.rerun()
