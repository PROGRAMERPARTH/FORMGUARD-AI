"""
FORMGUARD AI - Document Upload Page
Scheme selection and document upload with validation.
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
from modules.security import validate_file


def render_upload():
    """Render the scheme selection and document upload page."""
    # Header
    st.markdown("""
    <div class="formguard-header">
        <h1>📤 Scheme Selection & Document Upload</h1>
        <div class="tagline">Select your scheme and upload required documents</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Step 1: Scheme Selection ──
    st.markdown("### Step 1: Select Government Scheme")

    col1, col2 = st.columns(2)

    with col1:
        scheme_options = {sid: s["name"] for sid, s in SUPPORTED_SCHEMES.items()}
        selected_scheme = st.selectbox(
            "Government Scholarship Scheme",
            options=list(scheme_options.keys()),
            format_func=lambda x: scheme_options[x],
            help="Select the scholarship scheme you are applying for.",
        )

    scheme_data = SUPPORTED_SCHEMES[selected_scheme]

    with col2:
        selected_year = st.selectbox(
            "Academic Year",
            options=scheme_data["academic_years"],
            help="Select the academic year for your application.",
        )

    # Category selection if applicable
    selected_category = None
    if scheme_data.get("categories"):
        selected_category = st.selectbox(
            "Applicant Category",
            options=scheme_data["categories"],
            help="Select your category as per the scheme requirements.",
        )

    # Save selections to session state
    st.session_state.scheme_id = selected_scheme
    st.session_state.scheme_name = scheme_data["name"]
    st.session_state.academic_year = selected_year
    st.session_state.applicant_category = selected_category or ""

    # Initialize session ID if needed
    if not st.session_state.session_id:
        st.session_state.session_id = generate_session_id()

    # ── Scheme Info Card ──
    st.markdown(f"""
    <div class="info-card">
        <strong>📋 {scheme_data['name']}</strong><br>
        <span style="color: var(--text-secondary);">{scheme_data['description']}</span><br><br>
        <span style="font-size: 0.85rem;">
            🔗 <a href="{scheme_data.get('source_url', '#')}" target="_blank">Official Portal</a> |
            ❓ <a href="{scheme_data.get('faq_url', '#')}" target="_blank">FAQs</a>
        </span>
    </div>
    """, unsafe_allow_html=True)

    # ── Hackathon Demo Quick Loader ──
    demo_box, demo_btn = st.columns([3, 1])
    with demo_box:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1B2A4A, #2E5090); padding: 0.75rem 1rem; border-radius: 8px; color: white; margin-bottom: 0.5rem;">
            <strong>⚡ Hackathon Live Demo Mode</strong>: Test immediately with pre-configured synthetic scholarship documents (includes Name Variation & Academic Year check).
        </div>
        """, unsafe_allow_html=True)
    with demo_btn:
        if st.button("🚀 Load Demo Case", type="primary", use_container_width=True, help="Instantly load synthetic scholarship documents for live evaluation"):
            from modules.demo_generator import generate_all_demo_documents
            demo_docs = generate_all_demo_documents(str(TEMP_DIR))
            st.session_state.uploaded_documents = demo_docs
            st.session_state.scheme_id = "mahadbt_postmatric"
            st.session_state.academic_year = "2026-2027"
            st.session_state.applicant_category = "OBC"
            st.success("✅ Synthetic demo case loaded (5 documents)! Proceeding to Extraction...")
            st.session_state.current_page = "extraction"
            st.rerun()

    st.markdown("---")

    # ── Step 2: Document Upload ──
    st.markdown("### Step 2: Upload Documents")

    # Show required vs optional documents
    required_docs = scheme_data.get("required_documents", [])
    optional_docs = scheme_data.get("optional_documents", [])

    col_req, col_opt = st.columns(2)
    with col_req:
        st.markdown("**Required Documents:**")
        for doc_type in required_docs:
            doc_info = DOCUMENT_TYPES.get(doc_type, {})
            uploaded = doc_type in st.session_state.uploaded_documents
            icon = "✅" if uploaded else "⬜"
            st.markdown(f"{icon} {doc_info.get('display_name', doc_type)}")

    with col_opt:
        st.markdown("**Optional Documents:**")
        for doc_type in optional_docs:
            doc_info = DOCUMENT_TYPES.get(doc_type, {})
            uploaded = doc_type in st.session_state.uploaded_documents
            icon = "✅" if uploaded else "⬜"
            st.markdown(f"{icon} {doc_info.get('display_name', doc_type)}")

    st.markdown("<br>", unsafe_allow_html=True)

    # File upload section
    st.markdown(f"""
    <div class="info-card">
        📎 Accepted formats: <strong>PDF, JPG, JPEG, PNG</strong> | Max size: <strong>{MAX_FILE_SIZE_MB} MB per file</strong>
    </div>
    """, unsafe_allow_html=True)

    # Create upload sections for each document type
    all_doc_types = required_docs + optional_docs

    # Use tabs for organized upload
    if all_doc_types:
        tabs = st.tabs([
            f"{'📌 ' if dt in required_docs else ''}{DOCUMENT_TYPES.get(dt, {}).get('display_name', dt)}"
            for dt in all_doc_types
        ])

        for tab, doc_type in zip(tabs, all_doc_types):
            with tab:
                doc_info = DOCUMENT_TYPES.get(doc_type, {})
                is_required = doc_type in required_docs

                st.markdown(f"**{doc_info.get('file_label', doc_info.get('display_name', doc_type))}**")
                if is_required:
                    st.markdown("🔴 *Required for this scheme*")
                else:
                    st.markdown("🔵 *Optional*")

                # Expected fields info
                expected_fields = doc_info.get("expected_fields", [])
                if expected_fields:
                    with st.expander("ℹ️ Expected fields in this document"):
                        for field in expected_fields:
                            st.markdown(f"- {field.replace('_', ' ').title()}")

                # File uploader
                uploaded_file = st.file_uploader(
                    f"Upload {doc_info.get('display_name', doc_type)}",
                    type=ALLOWED_EXTENSIONS,
                    key=f"upload_{doc_type}",
                    help=f"Upload your {doc_info.get('display_name', doc_type)}. Accepted: PDF, JPG, JPEG, PNG.",
                    label_visibility="collapsed",
                )

                if uploaded_file is not None:
                    file_content = uploaded_file.read()
                    uploaded_file.seek(0)  # Reset for potential re-read

                    # Validate file
                    is_valid, validation_msg = validate_file(file_content, uploaded_file.name)

                    if is_valid:
                        # Save to temp directory
                        safe_name = sanitize_filename(uploaded_file.name)
                        file_path = save_temp_file(file_content, safe_name, str(TEMP_DIR))
                        file_hash = get_file_hash(file_content)

                        # Check for duplicates across all uploaded documents
                        is_duplicate = False
                        for existing_type, existing_info in st.session_state.uploaded_documents.items():
                            if existing_info.get("file_hash") == file_hash and existing_type != doc_type:
                                is_duplicate = True
                                st.warning(f"⚠️ This file appears to be the same as the uploaded {DOCUMENT_TYPES.get(existing_type, {}).get('display_name', existing_type)}.")
                                break

                        # Store document info
                        st.session_state.uploaded_documents[doc_type] = {
                            "file_name": uploaded_file.name,
                            "file_path": file_path,
                            "file_size": len(file_content),
                            "file_hash": file_hash,
                            "mime_type": uploaded_file.type,
                            "document_type": doc_type,
                            "upload_time": datetime.now().isoformat(),
                            "is_duplicate": is_duplicate,
                        }

                        st.success(f"✅ {uploaded_file.name} uploaded successfully ({format_file_size(len(file_content))})")

                        # Show file preview for images
                        if uploaded_file.type in ["image/jpeg", "image/png"]:
                            with st.expander("👁️ Preview"):
                                st.image(uploaded_file, width=400)
                    else:
                        st.error(f"❌ {validation_msg}")

                # Show already uploaded file info
                elif doc_type in st.session_state.uploaded_documents:
                    doc = st.session_state.uploaded_documents[doc_type]
                    st.info(f"📄 Previously uploaded: **{doc['file_name']}** ({format_file_size(doc['file_size'])})")
                    if st.button(f"🗑️ Remove", key=f"remove_{doc_type}"):
                        # Clean up temp file
                        try:
                            if os.path.exists(doc["file_path"]):
                                os.remove(doc["file_path"])
                        except OSError:
                            pass
                        del st.session_state.uploaded_documents[doc_type]
                        st.rerun()

    # ── Upload Summary ──
    st.markdown("---")
    st.markdown("### 📊 Upload Summary")

    uploaded_count = len(st.session_state.uploaded_documents)
    required_count = len(required_docs)
    required_uploaded = sum(1 for dt in required_docs if dt in st.session_state.uploaded_documents)

    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.metric("Documents Uploaded", uploaded_count)
    with col_s2:
        st.metric("Required Documents", f"{required_uploaded}/{required_count}")
    with col_s3:
        total_size = sum(d["file_size"] for d in st.session_state.uploaded_documents.values())
        st.metric("Total Size", format_file_size(total_size))

    # Progress bar
    if required_count > 0:
        progress = required_uploaded / required_count
        st.progress(progress, text=f"Required documents: {required_uploaded}/{required_count} uploaded")

    # Missing required documents warning
    missing_required = [dt for dt in required_docs if dt not in st.session_state.uploaded_documents]
    if missing_required:
        st.warning("⚠️ **Missing required documents:**")
        for dt in missing_required:
            doc_info = DOCUMENT_TYPES.get(dt, {})
            st.markdown(f"  - {doc_info.get('display_name', dt)}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Navigation ──
    col_back, col_spacer, col_next = st.columns([1, 2, 1])

    with col_back:
        if st.button("← Back to Home", use_container_width=True):
            st.session_state.current_page = "landing"
            st.rerun()

    with col_next:
        can_proceed = uploaded_count > 0
        if st.button(
            "Extract Document Data →",
            type="primary",
            use_container_width=True,
            disabled=not can_proceed,
        ):
            st.session_state.current_page = "extraction"
            st.rerun()

        if not can_proceed:
            st.caption("Upload at least one document to proceed.")
