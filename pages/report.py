"""
FORMGUARD AI - Application Readiness Report Page
Generate and download official PDF preflight verification reports with full audit trail.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DOCUMENT_TYPES, DISCLAIMER
from modules.report_generator import ReportGenerator
from utils.helpers import generate_verification_id, format_file_size
from utils.ui_components import render_workflow_stepper


def render_report():
    """Render the report generation and download page."""
    # Render Workflow Stepper at top
    render_workflow_stepper("report")

    st.markdown("""
    <div class="formguard-header">
        <h1>📋 Preflight Application Readiness Report</h1>
        <div class="tagline">Official preflight audit report, cross-certificate matrix, and downloadable PDF certification</div>
    </div>
    """, unsafe_allow_html=True)

    verification_result = st.session_state.get("verification_result")
    extractions = st.session_state.get("extractions", {})

    if not verification_result:
        st.warning("⚠️ No verification results available yet. Please complete document verification first.")
        if st.button("← Go to Verification", type="primary"):
            st.session_state.current_page = "verification"
            st.rerun()
        return

    # ── Report Meta & Summary ──
    if "current_report_id" not in st.session_state or not st.session_state.current_report_id:
        st.session_state.current_report_id = generate_verification_id()

    verification_id = st.session_state.current_report_id
    scheme_name = verification_result.get("scheme_name", "MahaDBT Scholarship")
    academic_year = verification_result.get("academic_year", "2026-2027")
    category = verification_result.get("applicant_category", "General")
    readiness = verification_result.get("overall_readiness", 0)
    checks = verification_result.get("checks", [])

    badge_cls = 'badge-pass' if readiness >= 80 else 'badge-warning' if readiness >= 50 else 'badge-critical'
    status_text = 'PREFLIGHT READY' if readiness >= 80 else 'ACTION REQUIRED BEFORE SUBMISSION' if readiness >= 50 else 'SIGNIFICANT DISCREPANCIES DETECTED'

    st.markdown(f"""
    <div style="background: white; border: 1px solid var(--border); border-top: 4px solid #1B2A4A; border-radius: 12px; padding: 1.5rem 1.75rem; margin-bottom: 1.5rem; box-shadow: var(--shadow-sm);">
        <div style="display: flex; justify-content: space-between; align-items: start; flex-wrap: wrap; gap: 1rem;">
            <div>
                <span class="status-pill pill-info" style="font-size: 0.72rem; margin-bottom: 0.35rem;">OFFICIAL PREFLIGHT AUDIT</span>
                <h3 style="margin: 0.25rem 0 0.2rem; color: #1B2A4A; font-size: 1.35rem;">FORMGUARD AI Preflight Certificate</h3>
                <div style="color: #64748B; font-size: 0.82rem;">
                    Audit Reference ID: <code>{verification_id}</code> • Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}
                </div>
            </div>
            <div style="text-align: right;">
                <span class="badge {badge_cls}" style="font-size: 0.85rem; padding: 0.45rem 1rem;">
                    {status_text}
                </span>
                <div style="font-size: 1.6rem; font-weight: 800; color: #1E293B; margin-top: 0.35rem;">
                    {readiness:.0f}% <span style="font-size: 0.85rem; font-weight: 500; color: #64748B;">Readiness</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Summary Grid ──
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📋 Application Profile")
        st.markdown(f"""
        | Parameter | Audit Record |
        |:---|:---|
        | **Government Scheme** | {scheme_name} |
        | **Target Academic Year** | {academic_year} |
        | **Reservation Category** | {category or 'General'} |
        | **Audited Certificates** | {verification_result.get('documents_processed', 0)} files |
        | **Verification Timestamp** | {datetime.now().strftime('%d %B %Y')} |
        """)

    with col2:
        st.markdown("#### 📊 Verification Breakdown")
        st.markdown(f"""
        | Audit Category | Outcome |
        |:---|:---|
        | 🟢 **Passed Criteria** | {verification_result.get('pass_count', 0)} checks |
        | 🟡 **Warnings & Discrepancies** | {verification_result.get('warning_count', 0)} checks |
        | 🔴 **Critical Missing Rules** | {verification_result.get('critical_count', 0)} checks |
        | 🔵 **Manual Review Items** | {verification_result.get('manual_review_count', 0)} checks |
        | **Overall Preflight Score** | **{readiness:.0f} / 100** |
        """)

    st.markdown("---")

    # ── Cross-Certificate Field Comparison Matrix ──
    st.markdown("#### 🔍 Cross-Certificate Field Comparison Matrix")
    st.caption("Side-by-side comparison of applicant data extracted across all submitted certificates:")

    if extractions:
        field_doc_map = {}
        for doc_type, extraction in extractions.items():
            doc_name = DOCUMENT_TYPES.get(doc_type, {}).get("display_name", doc_type)
            fields = extraction.get("extracted_fields", {})
            for field_name, field_data in fields.items():
                if field_name not in field_doc_map:
                    field_doc_map[field_name] = []
                val = field_data.get("value", "") if isinstance(field_data, dict) else str(field_data)
                conf = field_data.get("confidence", 0.8) if isinstance(field_data, dict) else 0.8
                field_doc_map[field_name].append({
                    "doc": doc_name,
                    "val": val,
                    "conf": conf
                })

        for f_name, entries in field_doc_map.items():
            clean_title = f_name.replace("_", " ").title()
            with st.expander(f"📌 {clean_title} — verified across {len(entries)} certificate(s)", expanded=(f_name in ["applicant_name", "academic_year"])):
                cols = st.columns(len(entries))
                for c, item in zip(cols, entries):
                    with c:
                        st.markdown(f"""
                        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 0.65rem 0.85rem;">
                            <div style="font-size: 0.75rem; color: #64748B; font-weight: 600;">{item['doc']}</div>
                            <div style="font-size: 0.95rem; font-weight: 700; color: #1E293B; margin: 0.25rem 0;"><code>{item['val']}</code></div>
                            <div style="font-size: 0.72rem; color: #10B981;">Confidence: {item['conf']:.0%}</div>
                        </div>
                        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Actionable Remediation Guidance ──
    st.markdown("#### ⚠️ Identified Preflight Action Items")
    issue_checks = [c for c in checks if c.get("severity") != "PASS"]

    if issue_checks:
        for idx, check in enumerate(issue_checks, 1):
            severity = check.get("severity", "WARNING")
            icon = "🔴" if severity == "CRITICAL" else "🟡" if severity == "WARNING" else "🔵"
            card_cls = "error-card" if severity == "CRITICAL" else "warning-card"

            st.markdown(f"""
            <div class="{card_cls}" style="margin-bottom: 0.65rem;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <strong>{idx}. {icon} {check.get('check_name', 'Check')}</strong> [{severity}]
                        <div style="color: #334155; font-size: 0.88rem; margin: 0.35rem 0 0.2rem;">
                            <strong>Finding:</strong> {check.get('reason', 'N/A')}
                        </div>
                        <div style="color: #1E3A8A; font-size: 0.85rem;">
                            💡 <strong>Action Required:</strong> {check.get('recommended_action', 'Review document.')}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("🎉 Outstanding! No issues detected. All cross-document checks and scheme eligibility rules passed.")

    # Disclaimer
    st.markdown("---")
    st.warning(f"⚠️ **Preflight Advisory:** {DISCLAIMER}")

    # ── PDF Report Generation & Download ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📥 Download Official PDF Verification Report")

    dl_col1, dl_col2, dl_col3 = st.columns([1, 2, 1])
    with dl_col2:
        if st.button("📄 Generate Official PDF Report", type="primary", use_container_width=True):
            with st.spinner("Compiling ReportLab PDF report with verification tables..."):
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
                        st.success("✅ Official PDF verification report generated successfully!")
                    else:
                        st.error("Failed to generate PDF report.")
                except Exception as e:
                    st.error(f"Error generating report: {str(e)}")

        # Persistent Download Button
        if st.session_state.get("generated_pdf_bytes"):
            pdf_data = st.session_state.generated_pdf_bytes
            st.download_button(
                label=f"⬇️ Download {st.session_state.get('generated_pdf_filename', 'Report.pdf')} ({format_file_size(len(pdf_data))})",
                data=pdf_data,
                file_name=st.session_state.get("generated_pdf_filename", f"FormGuard_Report_{verification_id}.pdf"),
                mime="application/pdf",
                use_container_width=True,
            )

    # ── Bottom Navigation ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    b_col1, b_col2, b_col3 = st.columns(3)

    with b_col1:
        if st.button("← Back to Verification", use_container_width=True):
            st.session_state.current_page = "verification"
            st.rerun()

    with b_col2:
        if st.button("📊 View Dashboard", use_container_width=True):
            st.session_state.current_page = "dashboard"
            st.rerun()

    with b_col3:
        if st.button("🚀 Start New Preflight", type="primary", use_container_width=True):
            st.session_state.session_id = None
            st.session_state.current_report_id = None
            st.session_state.uploaded_documents = {}
            st.session_state.extractions = {}
            st.session_state.verification_result = None
            st.session_state.chat_history = []
            st.session_state.generated_pdf_bytes = None
            st.session_state.current_page = "upload"
            st.rerun()
