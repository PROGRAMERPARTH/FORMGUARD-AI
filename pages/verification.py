"""
FORMGUARD AI - Cross-Document Verification Page
The core verification engine display with detailed results.
"""

import streamlit as st
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DOCUMENT_TYPES, SUPPORTED_SCHEMES, DISCLAIMER
from modules.validation_engine import ValidationEngine


def render_verification():
    """Render the cross-document verification page."""
    st.markdown("""
    <div class="formguard-header">
        <h1>✅ Cross-Document Verification</h1>
        <div class="tagline">Intelligent consistency checks across all your documents</div>
    </div>
    """, unsafe_allow_html=True)

    extractions = st.session_state.get("extractions", {})
    if not extractions:
        st.warning("⚠️ No document extractions available. Please extract document data first.")
        if st.button("← Go to Document Intelligence"):
            st.session_state.current_page = "extraction"
            st.rerun()
        return

    # ── Run Verification ──
    verification_result = st.session_state.get("verification_result")

    if not verification_result:
        st.markdown("""
        <div class="info-card">
            <strong>🔍 Ready to Verify</strong><br>
            Click below to run cross-document verification. The system will check for:
            <ul>
                <li>Name consistency across all documents</li>
                <li>Date and academic year validity</li>
                <li>Required document presence</li>
                <li>Missing fields and information gaps</li>
                <li>Certificate validity rules</li>
                <li>Scheme-specific requirements</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        if st.button("✅ Run Cross-Document Verification", type="primary", use_container_width=True):
            _run_verification(extractions)
            st.rerun()
    else:
        if st.button("🔄 Re-run Verification"):
            st.session_state.verification_result = None
            _run_verification(extractions)
            st.rerun()

    # ── Display Results ──
    if verification_result:
        st.markdown("---")

        # ── Summary Metrics ──
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="metric-card" style="border-left: 4px solid #10B981;">
                <div class="metric-value" style="color: #10B981;">{verification_result.get('pass_count', 0)}</div>
                <div class="metric-label">Passed</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card" style="border-left: 4px solid #F59E0B;">
                <div class="metric-value" style="color: #F59E0B;">{verification_result.get('warning_count', 0)}</div>
                <div class="metric-label">Warnings</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card" style="border-left: 4px solid #EF4444;">
                <div class="metric-value" style="color: #EF4444;">{verification_result.get('critical_count', 0)}</div>
                <div class="metric-label">Critical</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="metric-card" style="border-left: 4px solid #3B82F6;">
                <div class="metric-value" style="color: #3B82F6;">{verification_result.get('manual_review_count', 0)}</div>
                <div class="metric-label">Manual Review</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Overall Readiness ──
        readiness = verification_result.get("overall_readiness", 0)
        if readiness >= 80:
            readiness_color = "#10B981"
            readiness_label = "Good"
        elif readiness >= 50:
            readiness_color = "#F59E0B"
            readiness_label = "Needs Attention"
        else:
            readiness_color = "#EF4444"
            readiness_label = "Significant Issues"

        st.markdown(f"""
        <div class="info-card" style="border-left-color: {readiness_color};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong style="font-size: 1.1rem;">Application Readiness: {readiness:.0f}%</strong>
                    <br><span style="color: var(--text-secondary);">Status: {readiness_label}</span>
                </div>
                <div style="font-size: 2rem;">{
                    '✅' if readiness >= 80 else '⚠️' if readiness >= 50 else '❌'
                }</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.progress(readiness / 100)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Detailed Results ──
        st.markdown("### 📋 Detailed Verification Results")

        checks = verification_result.get("checks", [])

        # Filter options
        filter_col1, filter_col2 = st.columns([1, 3])
        with filter_col1:
            severity_filter = st.selectbox(
                "Filter by severity",
                options=["All", "CRITICAL", "WARNING", "MANUAL_REVIEW", "PASS"],
            )

        # Sort: Critical first, then Warning, then Manual Review, then Pass
        severity_order = {"CRITICAL": 0, "WARNING": 1, "MANUAL_REVIEW": 2, "PASS": 3}
        sorted_checks = sorted(checks, key=lambda c: severity_order.get(c.get("severity", "PASS"), 4))

        if severity_filter != "All":
            sorted_checks = [c for c in sorted_checks if c.get("severity") == severity_filter]

        for check in sorted_checks:
            severity = check.get("severity", "PASS")

            # Style based on severity
            styles = {
                "CRITICAL": ("error-card", "🔴", "#EF4444"),
                "WARNING": ("warning-card", "🟡", "#F59E0B"),
                "MANUAL_REVIEW": ("info-card", "🔵", "#3B82F6"),
                "PASS": ("success-card", "🟢", "#10B981"),
            }
            card_class, icon, color = styles.get(severity, ("info-card", "⚪", "#64748B"))

            with st.expander(f"{icon} {check.get('check_name', 'Check')} — {severity}", expanded=(severity in ["CRITICAL", "WARNING"])):
                st.markdown(f"**Field Checked:** {check.get('field_checked', 'N/A')}")

                # Document sources
                sources = check.get("document_sources", [])
                if sources:
                    source_names = [DOCUMENT_TYPES.get(s, {}).get("display_name", s) for s in sources]
                    st.markdown(f"**Documents:** {', '.join(source_names)}")

                # Extracted values
                values = check.get("extracted_values", {})
                if values:
                    st.markdown("**Extracted Values:**")
                    for doc, val in values.items():
                        doc_name = DOCUMENT_TYPES.get(doc, {}).get("display_name", doc)
                        st.markdown(f"  - *{doc_name}*: `{val}`")

                # Comparison result
                if check.get("comparison_result"):
                    st.markdown(f"**Result:** {check['comparison_result']}")

                # Reason
                st.markdown(f"**Reason:** {check.get('reason', 'N/A')}")

                # Recommended action
                if check.get("recommended_action"):
                    st.info(f"💡 **Recommended Action:** {check['recommended_action']}")

        # ── Checklist Summary ──
        st.markdown("---")
        st.markdown("### ✅ Application Readiness Checklist")

        # Group checks by category
        pass_checks = [c for c in checks if c.get("severity") == "PASS"]
        issue_checks = [c for c in checks if c.get("severity") != "PASS"]

        for check in pass_checks:
            st.markdown(f"""
            <div class="checklist-item checklist-pass">
                ✅ {check.get('check_name', 'Check')}
            </div>
            """, unsafe_allow_html=True)

        for check in issue_checks:
            severity = check.get("severity", "WARNING")
            cls = "checklist-fail" if severity == "CRITICAL" else "checklist-warning"
            icon = "❌" if severity == "CRITICAL" else "⚠️" if severity == "WARNING" else "🔍"
            st.markdown(f"""
            <div class="checklist-item {cls}">
                {icon} {check.get('check_name', 'Check')} — <em>{check.get('reason', '')}</em>
            </div>
            """, unsafe_allow_html=True)

        # Disclaimer
        st.markdown("---")
        st.caption(f"⚠️ {DISCLAIMER}")

    # ── Navigation ──
    st.markdown("<br>", unsafe_allow_html=True)
    col_back, col_assistant, col_report = st.columns(3)

    with col_back:
        if st.button("← Back to Extraction", use_container_width=True):
            st.session_state.current_page = "extraction"
            st.rerun()

    with col_assistant:
        if st.button("🤖 AI Assistant", use_container_width=True, disabled=not verification_result):
            st.session_state.current_page = "assistant"
            st.rerun()

    with col_report:
        if st.button("📋 Generate Report →", type="primary", use_container_width=True, disabled=not verification_result):
            st.session_state.current_page = "report"
            st.rerun()


def _run_verification(extractions: dict):
    """Run the cross-document verification engine."""
    progress = st.progress(0, text="Initializing verification engine...")

    start_time = time.time()

    scheme_id = st.session_state.get("scheme_id", "mahadbt_postmatric")
    academic_year = st.session_state.get("academic_year", "")
    category = st.session_state.get("applicant_category", "")
    scheme_data = SUPPORTED_SCHEMES.get(scheme_id, {})

    engine = ValidationEngine(
        scheme_id=scheme_id,
        scheme_data=scheme_data,
        academic_year=academic_year,
        applicant_category=category,
    )

    progress.progress(0.2, text="Checking document presence...")

    # Run all checks
    checks = []

    # 1. Required document presence checks
    presence_checks = engine.check_required_documents(extractions)
    checks.extend(presence_checks)
    progress.progress(0.35, text="Checking name consistency...")

    # 2. Name consistency checks
    name_checks = engine.check_name_consistency(extractions)
    checks.extend(name_checks)
    progress.progress(0.50, text="Checking date consistency...")

    # 3. Date and academic year checks
    date_checks = engine.check_date_consistency(extractions)
    checks.extend(date_checks)
    progress.progress(0.65, text="Checking missing fields...")

    # 4. Missing field checks
    field_checks = engine.check_missing_fields(extractions)
    checks.extend(field_checks)
    progress.progress(0.80, text="Running scheme-specific checks...")

    # 5. Scheme-specific checks
    scheme_checks = engine.check_scheme_requirements(extractions)
    checks.extend(scheme_checks)
    progress.progress(0.90, text="Checking for duplicates...")

    # 6. Duplicate document detection
    dup_checks = engine.check_duplicate_documents(st.session_state.get("uploaded_documents", {}))
    checks.extend(dup_checks)

    # Compute counts
    pass_count = sum(1 for c in checks if c["severity"] == "PASS")
    warning_count = sum(1 for c in checks if c["severity"] == "WARNING")
    critical_count = sum(1 for c in checks if c["severity"] == "CRITICAL")
    manual_review_count = sum(1 for c in checks if c["severity"] == "MANUAL_REVIEW")
    total = len(checks)

    overall_readiness = round((pass_count / total * 100), 1) if total > 0 else 0

    processing_time = time.time() - start_time

    verification_result = {
        "session_id": st.session_state.get("session_id", ""),
        "scheme_id": scheme_id,
        "scheme_name": scheme_data.get("name", "Unknown"),
        "academic_year": academic_year,
        "applicant_category": category,
        "documents_processed": len(extractions),
        "checks": checks,
        "pass_count": pass_count,
        "warning_count": warning_count,
        "critical_count": critical_count,
        "manual_review_count": manual_review_count,
        "overall_readiness": overall_readiness,
        "processing_time": processing_time,
    }

    st.session_state.verification_result = verification_result

    # Update stats
    st.session_state.total_issues_found = (
        st.session_state.get("total_issues_found", 0) + warning_count + critical_count
    )

    # Add to session history
    sessions = st.session_state.get("sessions_history", [])
    sessions.append({
        "scheme_name": scheme_data.get("name", "Unknown"),
        "academic_year": academic_year,
        "docs_count": len(extractions),
        "status": "completed",
        "readiness": overall_readiness,
    })
    st.session_state.sessions_history = sessions

    progress.progress(1.0, text=f"Verification complete! ({processing_time:.1f}s)")
