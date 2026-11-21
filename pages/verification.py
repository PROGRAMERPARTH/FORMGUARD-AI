"""
FORMGUARD AI - Cross-Document Verification Page
The core verification engine display with interactive filtering, AI jump, and remediation checklist.
"""

import streamlit as st
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DOCUMENT_TYPES, SUPPORTED_SCHEMES, DISCLAIMER
from modules.validation_engine import ValidationEngine
from utils.ui_components import render_workflow_stepper


def render_verification():
    """Render the cross-document verification page."""
    # Render Workflow Stepper at top
    render_workflow_stepper("verification")

    st.markdown("""
    <div class="formguard-header">
        <h1>✅ Cross-Document Verification Engine</h1>
        <div class="tagline">Deterministic cross-document consistency checks, scheme rule matching, and preflight audit</div>
    </div>
    """, unsafe_allow_html=True)

    extractions = st.session_state.get("extractions", {})
    if not extractions:
        st.warning("⚠️ No document extractions available. Please extract document data first.")
        if st.button("← Go to Document Intelligence", type="primary"):
            st.session_state.current_page = "extraction"
            st.rerun()
        return

    # ── Run Verification ──
    verification_result = st.session_state.get("verification_result")

    if not verification_result:
        st.markdown("""
        <div class="info-card">
            <h4 style="margin: 0 0 0.5rem; color: #1B2A4A;">🔍 Ready for Cross-Document Preflight Audit</h4>
            <p style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 0.75rem;">
                The validation engine runs 8 deterministic checks against official MahaDBT rules:
            </p>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.85rem; color: #334155;">
                <div>✓ Cross-certificate Name & Initials Consistency</div>
                <div>✓ Academic Year & Bonafide Alignment</div>
                <div>✓ Mandatory Document Presence</div>
                <div>✓ Caste & Income Eligibility Thresholds</div>
                <div>✓ Duplicate Document Detection</div>
                <div>✓ Critical Field Completeness</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("✅ Run Preflight Verification", type="primary", use_container_width=True):
            _run_verification(extractions)
            st.rerun()
    else:
        v_col1, v_col2 = st.columns([3, 1])
        with v_col1:
            st.caption("Verification completed. Filter checks below or click 'Explain with AI' on any flagged issue.")
        with v_col2:
            if st.button("🔄 Re-run Verification", use_container_width=True):
                st.session_state.verification_result = None
                _run_verification(extractions)
                st.rerun()

    # ── Display Results ──
    if verification_result:
        st.markdown("---")

        # ── Summary Metrics ──
        col1, col2, col3, col4 = st.columns(4)

        pass_c = verification_result.get("pass_count", 0)
        warn_c = verification_result.get("warning_count", 0)
        crit_c = verification_result.get("critical_count", 0)
        man_c = verification_result.get("manual_review_count", 0)

        with col1:
            st.markdown(f"""
            <div class="metric-card" style="border-top: 3px solid #10B981;">
                <div class="metric-value" style="color: #10B981;">{pass_c}</div>
                <div class="metric-label">Passed Checks</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card" style="border-top: 3px solid #F59E0B;">
                <div class="metric-value" style="color: #F59E0B;">{warn_c}</div>
                <div class="metric-label">Warnings</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card" style="border-top: 3px solid #EF4444;">
                <div class="metric-value" style="color: #EF4444;">{crit_c}</div>
                <div class="metric-label">Critical Issues</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="metric-card" style="border-top: 3px solid #3B82F6;">
                <div class="metric-value" style="color: #3B82F6;">{man_c}</div>
                <div class="metric-label">Manual Review</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Overall Readiness Banner ──
        readiness = verification_result.get("overall_readiness", 0)
        if readiness >= 80:
            readiness_color = "#10B981"
            readiness_title = "EXCELLENT PREFLIGHT READINESS"
            readiness_desc = "Your documents meet major consistency requirements. Review minor suggestions before portal submission."
            status_icon = "🟢"
        elif readiness >= 50:
            readiness_color = "#F59E0B"
            readiness_title = "ACTION REQUIRED BEFORE SUBMISSION"
            readiness_desc = "Detected discrepancies (e.g. name variations or academic year mismatch) that could delay or reject your scholarship."
            status_icon = "🟡"
        else:
            readiness_color = "#EF4444"
            readiness_title = "CRITICAL DISCREPANCIES DETECTED"
            readiness_desc = "High rejection probability on MahaDBT portal. Mandatory documents or eligibility criteria are missing."
            status_icon = "🔴"

        st.markdown(f"""
        <div style="background: white; border: 1px solid var(--border); border-left: 6px solid {readiness_color}; border-radius: 12px; padding: 1.25rem 1.75rem; margin-bottom: 1.5rem; box-shadow: var(--shadow-sm);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                <div>
                    <div style="font-size: 0.8rem; font-weight: 700; color: {readiness_color}; text-transform: uppercase; letter-spacing: 0.05em;">
                        {status_icon} {readiness_title}
                    </div>
                    <div style="font-size: 1.4rem; font-weight: 800; color: #1E293B; margin: 0.2rem 0;">
                        Readiness Score: {readiness:.0f}%
                    </div>
                    <div style="color: #64748B; font-size: 0.88rem;">{readiness_desc}</div>
                </div>
                <div style="text-align: right;">
                    <span class="badge {'badge-pass' if readiness >= 80 else 'badge-warning' if readiness >= 50 else 'badge-critical'}" style="font-size: 0.9rem; padding: 0.5rem 1rem;">
                        {readiness:.0f}% COMPLIANT
                    </span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.progress(readiness / 100.0)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Interactive Severity Filter Bar ──
        st.markdown("### 📋 Verification Checks Audit")

        checks = verification_result.get("checks", [])

        # Filter Pills
        filter_col, search_col = st.columns([3, 2])
        with filter_col:
            selected_filter = st.radio(
                "Filter Checks",
                options=["All", "CRITICAL", "WARNING", "MANUAL_REVIEW", "PASS"],
                format_func=lambda x: f"All ({len(checks)})" if x == "All" else f"{x} ({sum(1 for c in checks if c.get('severity') == x)})",
                horizontal=True,
                label_visibility="collapsed"
            )

        with search_col:
            kw = st.text_input("Filter by keyword", placeholder="e.g. Name, Year, Domicile...", label_visibility="collapsed").strip().lower()

        # Filter and sort
        severity_order = {"CRITICAL": 0, "WARNING": 1, "MANUAL_REVIEW": 2, "PASS": 3}
        filtered_checks = sorted(checks, key=lambda c: severity_order.get(c.get("severity", "PASS"), 4))

        if selected_filter != "All":
            filtered_checks = [c for c in filtered_checks if c.get("severity") == selected_filter]

        if kw:
            filtered_checks = [
                c for c in filtered_checks
                if kw in c.get("check_name", "").lower()
                or kw in c.get("reason", "").lower()
                or kw in c.get("field_checked", "").lower()
            ]

        # Render Check Cards
        if not filtered_checks:
            st.info("No checks match the selected filter.")

        for i, check in enumerate(filtered_checks):
            severity = check.get("severity", "PASS")
            check_id = check.get("check_id", str(i))

            # Style classes
            styles = {
                "CRITICAL": ("error-card", "🔴", "badge-critical"),
                "WARNING": ("warning-card", "🟡", "badge-warning"),
                "MANUAL_REVIEW": ("info-card", "🔵", "badge-review"),
                "PASS": ("success-card", "🟢", "badge-pass"),
            }
            card_class, icon, badge_class = styles.get(severity, ("info-card", "⚪", "badge-review"))

            is_open = severity in ["CRITICAL", "WARNING"]
            with st.expander(f"{icon} {check.get('check_name', 'Check')} — {severity}", expanded=is_open):
                st.markdown(f"**Field Verified:** `{check.get('field_checked', 'General')}`")

                # Document sources
                sources = check.get("document_sources", [])
                if sources:
                    source_names = [DOCUMENT_TYPES.get(s, {}).get("display_name", s) for s in sources]
                    st.markdown(f"**Document Sources:** {', '.join(source_names)}")

                # Extracted values
                values = check.get("extracted_values", {})
                if values:
                    st.markdown("**Values Compared:**")
                    for doc, val in values.items():
                        doc_name = DOCUMENT_TYPES.get(doc, {}).get("display_name", doc)
                        st.markdown(f"  - *{doc_name}*: `{val}`")

                # Comparison result & reason
                if check.get("comparison_result"):
                    st.markdown(f"**Comparison Detail:** {check['comparison_result']}")

                st.markdown(f"**Audit Findings:** {check.get('reason', 'N/A')}")

                # Recommended action
                if check.get("recommended_action"):
                    st.info(f"💡 **Recommended Action:** {check['recommended_action']}")

                # Interactive Action Bar inside issue
                if severity in ["CRITICAL", "WARNING", "MANUAL_REVIEW"]:
                    act_c1, act_c2 = st.columns([2, 1])
                    with act_c2:
                        chk_key = f"chk_ai_{check_id}"
                        if st.button("🤖 Explain with AI", key=chk_key, use_container_width=True):
                            from pages.assistant import _explain_issue_in_chat
                            _explain_issue_in_chat(check, st.session_state.get("language", "en"))
                            st.session_state.current_page = "assistant"
                            st.rerun()

        # ── Interactive Remediation Tracker ──
        st.markdown("---")
        st.markdown("### 📝 Applicant Remediation Tracker")
        st.caption("Check off items as you fix them in your official application documents before final portal submission:")

        issue_checks = [c for c in checks if c.get("severity") != "PASS"]
        if issue_checks:
            for c in issue_checks:
                cid = c.get("check_id", c.get("check_name"))
                cur_remedied = st.session_state.remediation_status.get(cid, False)
                remedied = st.checkbox(
                    f"Resolved: {c.get('check_name')} ({c.get('severity')})",
                    value=cur_remedied,
                    key=f"rem_{cid}"
                )
                st.session_state.remediation_status[cid] = remedied
        else:
            st.success("🎉 All verification checks passed! No remediation necessary.")

        # Disclaimer
        st.markdown("---")
        st.caption(f"⚠️ {DISCLAIMER}")

    # ── Bottom Navigation ──
    st.markdown("<br>", unsafe_allow_html=True)
    nav_col1, nav_col2, nav_col3 = st.columns([1, 1.5, 1.2])

    with nav_col1:
        if st.button("← Back to Extraction", use_container_width=True):
            st.session_state.current_page = "extraction"
            st.rerun()

    with nav_col2:
        if st.button("🤖 Consult AI Assistant", use_container_width=True, disabled=not verification_result):
            st.session_state.current_page = "assistant"
            st.rerun()

    with nav_col3:
        if st.button("Generate Report ➡️", type="primary", use_container_width=True, disabled=not verification_result):
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
    checks = []

    # 1. Required document presence
    checks.extend(engine.check_required_documents(extractions))
    progress.progress(0.35, text="Checking name consistency...")

    # 2. Name consistency checks
    checks.extend(engine.check_name_consistency(extractions))
    progress.progress(0.50, text="Checking date & academic year consistency...")

    # 3. Date and academic year checks
    checks.extend(engine.check_date_consistency(extractions))
    progress.progress(0.65, text="Checking missing fields...")

    # 4. Missing field checks
    checks.extend(engine.check_missing_fields(extractions))
    progress.progress(0.80, text="Running scheme-specific checks...")

    # 5. Scheme-specific checks
    checks.extend(engine.check_scheme_requirements(extractions))
    progress.progress(0.90, text="Checking duplicate documents...")

    # 6. Duplicate document detection
    checks.extend(engine.check_duplicate_documents(st.session_state.get("uploaded_documents", {})))

    # Compute metrics
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
    st.session_state.total_issues_found = (
        st.session_state.get("total_issues_found", 0) + warning_count + critical_count
    )

    # Add to sessions history
    sessions = st.session_state.get("sessions_history", [])
    sessions.append({
        "scheme_name": scheme_data.get("name", "Unknown"),
        "academic_year": academic_year,
        "docs_count": len(extractions),
        "status": "completed",
        "readiness": overall_readiness,
    })
    st.session_state.sessions_history = sessions

    progress.progress(1.0, text=f"Verification complete in {processing_time:.2f}s!")
