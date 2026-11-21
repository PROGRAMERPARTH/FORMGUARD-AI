"""
FORMGUARD AI - Document Upload Page
Scheme selection and document upload with validation and live completeness tracking.
"""

import streamlit as st
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    SUPPORTED_SCHEMES, DOCUMENT_TYPES, MAX_FILE_SIZE_MB,
    MAX_FILE_SIZE_BYTES, ALLOWED_EXTENSIONS, TEMP_DIR
)
from utils.helpers import (
    generate_session_id, validate_file_type, validate_file_size,
    format_file_size, save_temp_file, get_file_hash, sanitize_filename
)
from utils.ui_components import render_workflow_stepper
from modules.security import validate_file


def render_upload():
    """Render the scheme selection and document upload page."""
    # Render Workflow Stepper at top
    render_workflow_stepper("upload")

    # Header Banner
    st.markdown("""
    <div class="formguard-header">
        <h1>📤 Scheme Selection & Document Upload</h1>
        <div class="tagline">Select your welfare scheme and upload application certificates for preflight validation</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Hackathon Demo Quick Loader ──
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1B2A4A 0%, #2E5090 100%); padding: 1.25rem 1.5rem; border-radius: 12px; color: white; margin-bottom: 1.5rem; box-shadow: 0 4px 12px rgba(46, 80, 144, 0.25); border: 1px solid rgba(255,255,255,0.15);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
            <div>
                <span class="status-pill pill-warning" style="margin-bottom: 0.35rem;">⚡ Hackathon Fast-Track Evaluation</span>
                <h4 style="color: white !important; margin: 0.25rem 0 0.2rem; font-size: 1.15rem;">1-Click Demo Case: Rahul Suresh Patil</h4>
                <p style="color: rgba(255,255,255,0.85); font-size: 0.85rem; margin: 0; line-height: 1.4;">
                    Instantly load 5 synthetic scholarship PDFs containing realistic test challenges:
                    <strong>Bank Name Initials variation</strong> (<code>R. S. Patil</code>), <strong>Missing Domicile Certificate</strong>, and <strong>Bonafide Year Discrepancy</strong>.
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    demo_btn_col1, demo_btn_col2 = st.columns([3, 1])
    with demo_btn_col2:
        if st.button("🚀 Load Synthetic Demo Case", type="primary", use_container_width=True, help="Instantly load pre-generated test documents for live evaluation"):
            from modules.demo_generator import generate_all_demo_documents
            demo_docs = generate_all_demo_documents(str(TEMP_DIR))
            st.session_state.uploaded_documents = demo_docs
            st.session_state.scheme_id = "mahadbt_postmatric"
            st.session_state.scheme_name = "MahaDBT Post-Matric Scholarship"
            st.session_state.academic_year = "2026-2027"
            st.session_state.applicant_category = "OBC"
            # Reset downstream states to force fresh verification run
            st.session_state.extractions = {}
            st.session_state.verification_result = None
            st.success("✅ Synthetic demo case loaded (5 documents)! Proceeding to Extraction...")
            st.session_state.current_page = "extraction"
            st.rerun()

    st.markdown("---")

    # ── Step 1: Scheme Selection ──
    st.markdown("### Step 1: Select Government Scheme & Profile")

    col1, col2, col3 = st.columns(3)

    with col1:
        scheme_options = {sid: s["name"] for sid, s in SUPPORTED_SCHEMES.items()}
        selected_scheme = st.selectbox(
            "Scholarship Scheme",
            options=list(scheme_options.keys()),
            format_func=lambda x: scheme_options[x],
            help="Select the scholarship scheme you are applying for on MahaDBT.",
        )

    scheme_data = SUPPORTED_SCHEMES[selected_scheme]

    with col2:
        selected_year = st.selectbox(
            "Target Academic Year",
            options=scheme_data["academic_years"],
            index=0 if "2026-2027" in scheme_data["academic_years"] else 0,
            help="Select the academic year of your current scholarship application.",
        )

    with col3:
        categories = scheme_data.get("categories", ["General", "OBC", "SC", "ST", "VJNT", "SBC", "EWS"])
        selected_category = st.selectbox(
            "Applicant Category",
            options=categories,
            index=categories.index("OBC") if "OBC" in categories else 0,
            help="Select your social reservation category as per government records.",
        )

    # Save selections to session state
    st.session_state.scheme_id = selected_scheme
    st.session_state.scheme_name = scheme_data["name"]
    st.session_state.academic_year = selected_year
    st.session_state.applicant_category = selected_category

    # Initialize session ID if needed
    if not st.session_state.session_id:
        st.session_state.session_id = generate_session_id()

    # ── Live Completeness Tracker ──
    required_docs = scheme_data.get("required_documents", [])
    optional_docs = scheme_data.get("optional_documents", [])
    all_doc_types = required_docs + optional_docs

    uploaded_dict = st.session_state.uploaded_documents
    required_uploaded_count = sum(1 for dt in required_docs if dt in uploaded_dict)
    total_required = len(required_docs)
    completeness_pct = (required_uploaded_count / total_required * 100) if total_required > 0 else 0

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Step 2: Upload Application Documents")

    # Interactive Checklist / Progress Pill Bar
    st.markdown(f"""
    <div style="background: white; border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem 1.5rem; margin-bottom: 1.5rem; box-shadow: var(--shadow-sm);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
            <div>
                <strong style="color: #1B2A4A; font-size: 1rem;">Document Readiness: {completeness_pct:.0f}% Complete</strong>
                <div style="color: #64748B; font-size: 0.82rem;">{required_uploaded_count} of {total_required} mandatory documents uploaded for {scheme_data['name']}</div>
            </div>
            <div>
                <span class="badge {'badge-pass' if required_uploaded_count == total_required else 'badge-warning'}">
                    {'ALL REQUIRED READY' if required_uploaded_count == total_required else f'{total_required - required_uploaded_count} MISSING'}
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.progress(completeness_pct / 100.0)

    # ── Tabbed Upload Section ──
    tabs = st.tabs([
        f"{'✅ ' if dt in uploaded_dict else ('🔴 ' if dt in required_docs else '⚪ ')}{DOCUMENT_TYPES.get(dt, {}).get('display_name', dt)}"
        for dt in all_doc_types
    ])

    for tab, doc_type in zip(tabs, all_doc_types):
        with tab:
            doc_info = DOCUMENT_TYPES.get(doc_type, {})
            is_required = doc_type in required_docs
            is_uploaded = doc_type in uploaded_dict

            col_info, col_action = st.columns([2, 3])

            with col_info:
                st.markdown(f"#### {doc_info.get('display_name', doc_type)}")
                if is_required:
                    st.markdown('<span class="status-pill pill-error">Mandatory Document</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="status-pill pill-info">Optional Supporting Document</span>', unsafe_allow_html=True)

                st.markdown(f"<p style='color: #64748B; font-size: 0.85rem; margin-top: 0.5rem;'>{doc_info.get('file_label', '')}</p>", unsafe_allow_html=True)

                expected_fields = doc_info.get("expected_fields", [])
                if expected_fields:
                    with st.expander("🔍 Fields Verified from this Document", expanded=False):
                        for f in expected_fields:
                            st.markdown(f"- `{f.replace('_', ' ').title()}`")

            with col_action:
                if is_uploaded:
                    doc = uploaded_dict[doc_type]
                    st.markdown(f"""
                    <div class="success-card" style="margin-bottom: 0.75rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong style="color: #065F46;">✓ {doc['file_name']}</strong>
                                <div style="color: #64748B; font-size: 0.8rem; margin-top: 0.2rem;">
                                    Size: {format_file_size(doc['file_size'])} • SHA-256: <code>{doc.get('file_hash', '')[:12]}...</code>
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    btn_del_col1, btn_del_col2 = st.columns([3, 1])
                    with btn_del_col2:
                        if st.button("🗑️ Remove", key=f"del_{doc_type}", use_container_width=True):
                            try:
                                if os.path.exists(doc.get("file_path", "")):
                                    os.remove(doc["file_path"])
                            except OSError:
                                pass
                            del st.session_state.uploaded_documents[doc_type]
                            if doc_type in st.session_state.get("extractions", {}):
                                del st.session_state.extractions[doc_type]
                            st.rerun()

                else:
                    uploaded_file = st.file_uploader(
                        f"Choose file for {doc_info.get('display_name', doc_type)}",
                        type=ALLOWED_EXTENSIONS,
                        key=f"upload_{doc_type}",
                        help=f"Accepts PDF, JPG, PNG (Max {MAX_FILE_SIZE_MB}MB)",
                    )

                    if uploaded_file is not None:
                        file_content = uploaded_file.read()
                        uploaded_file.seek(0)

                        is_valid, validation_msg = validate_file(file_content, uploaded_file.name)
                        if is_valid:
                            safe_name = sanitize_filename(uploaded_file.name)
                            file_path = save_temp_file(file_content, safe_name, str(TEMP_DIR))
                            file_hash = get_file_hash(file_content)

                            # Check for duplicates across documents
                            is_dup = any(
                                existing_info.get("file_hash") == file_hash and existing_type != doc_type
                                for existing_type, existing_info in st.session_state.uploaded_documents.items()
                            )

                            st.session_state.uploaded_documents[doc_type] = {
                                "file_name": uploaded_file.name,
                                "file_path": file_path,
                                "file_size": len(file_content),
                                "file_hash": file_hash,
                                "mime_type": uploaded_file.type,
                                "document_type": doc_type,
                                "upload_time": datetime.now().isoformat(),
                                "is_duplicate": is_dup,
                            }
                            st.success(f"✅ {uploaded_file.name} uploaded successfully!")
                            st.rerun()
                        else:
                            st.error(f"❌ {validation_msg}")

    # ── Upload Summary & Navigation ──
    st.markdown("---")
    uploaded_total = len(st.session_state.uploaded_documents)

    sum_col1, sum_col2, sum_col3 = st.columns([1, 2, 1.2])

    with sum_col1:
        if st.button("← Back to Home", use_container_width=True):
            st.session_state.current_page = "landing"
            st.rerun()

    with sum_col2:
        missing_mandatory = [dt for dt in required_docs if dt not in st.session_state.uploaded_documents]
        if missing_mandatory:
            missing_names = ", ".join([DOCUMENT_TYPES.get(dt, {}).get("display_name", dt) for dt in missing_mandatory])
            st.warning(f"⚠️ Mandatory document missing: **{missing_names}**. You can proceed, but preflight will flag it.")
        elif uploaded_total > 0:
            st.success("🎉 All mandatory documents uploaded! You are ready for OCR Intelligence.")

    with sum_col3:
        can_proceed = uploaded_total > 0
        if st.button(
            f"Extract Data ({uploaded_total}) ➡️",
            type="primary",
            use_container_width=True,
            disabled=not can_proceed,
        ):
            st.session_state.current_page = "extraction"
            st.rerun()
