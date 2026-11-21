"""
FORMGUARD AI - Document Intelligence Page
OCR extraction and structured field display with user review and confidence meters.
"""

import streamlit as st
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DOCUMENT_TYPES
from modules.ocr_engine import extract_text_from_file
from modules.field_extractor import extract_fields_from_text
from utils.ui_components import render_workflow_stepper


def render_document_intelligence():
    """Render the document intelligence / OCR extraction page."""
    # Render Workflow Stepper at top
    render_workflow_stepper("extraction")

    st.markdown("""
    <div class="formguard-header">
        <h1>🔍 Document Intelligence</h1>
        <div class="tagline">Deterministic text extraction, OCR confidence scoring, and structured field recognition</div>
    </div>
    """, unsafe_allow_html=True)

    uploaded_docs = st.session_state.get("uploaded_documents", {})

    if not uploaded_docs:
        st.warning("⚠️ No documents uploaded yet. Please upload your application documents first.")
        if st.button("← Go to Upload Documents", type="primary"):
            st.session_state.current_page = "upload"
            st.rerun()
        return

    extractions = st.session_state.get("extractions", {})

    # ── Action Bar ──
    if not extractions:
        st.markdown(f"""
        <div class="info-card">
            <strong>📄 {len(uploaded_docs)} Document(s) Ready for Intelligence Processing</strong><br>
            <span style="color: var(--text-secondary); font-size: 0.9rem;">
                Click below to run PyMuPDF / Tesseract OCR. The pipeline extracts applicant names, certificate numbers,
                issuing authorities, financial limits, and academic years.
            </span>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔍 Extract Document Information", type="primary", use_container_width=True):
            _run_extraction(uploaded_docs)
            st.rerun()
    else:
        re_col1, re_col2 = st.columns([3, 1])
        with re_col1:
            st.caption("Review extracted fields below. You can edit any field to correct OCR misreadings before running verification.")
        with re_col2:
            if st.button("🔄 Re-run Extraction", use_container_width=True, help="Re-extract from scratch"):
                st.session_state.extractions = {}
                _run_extraction(uploaded_docs)
                st.rerun()

    # ── Display Extractions ──
    if extractions:
        # Calculate summary metrics
        total_fields = sum(len(ext.get("extracted_fields", {})) for ext in extractions.values())
        confidence_values = []
        for ext in extractions.values():
            for field_data in ext.get("extracted_fields", {}).values():
                if isinstance(field_data, dict) and "confidence" in field_data:
                    confidence_values.append(field_data["confidence"])
        avg_confidence = (sum(confidence_values) / len(confidence_values)) if confidence_values else 0

        # Metrics Row
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.markdown(f"""
            <div class="metric-card" style="border-top: 3px solid #1B2A4A;">
                <div class="metric-value">{len(extractions)}</div>
                <div class="metric-label">Documents Processed</div>
            </div>
            """, unsafe_allow_html=True)

        with m_col2:
            st.markdown(f"""
            <div class="metric-card" style="border-top: 3px solid #2E5090;">
                <div class="metric-value">{total_fields}</div>
                <div class="metric-label">Fields Identified</div>
            </div>
            """, unsafe_allow_html=True)

        with m_col3:
            conf_color = "#10B981" if avg_confidence >= 0.8 else "#F59E0B" if avg_confidence >= 0.6 else "#EF4444"
            st.markdown(f"""
            <div class="metric-card" style="border-top: 3px solid {conf_color};">
                <div class="metric-value" style="color: {conf_color};">{avg_confidence:.0%}</div>
                <div class="metric-label">Avg. OCR Confidence</div>
            </div>
            """, unsafe_allow_html=True)

        with m_col4:
            edited_count = sum(
                1 for ext in extractions.values()
                for fd in ext.get("extracted_fields", {}).values()
                if isinstance(fd, dict) and fd.get("is_user_confirmed")
            )
            st.markdown(f"""
            <div class="metric-card" style="border-top: 3px solid #3B82F6;">
                <div class="metric-value" style="color: #3B82F6;">{edited_count}</div>
                <div class="metric-label">User Overrides</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Quick Field Search / Filter
        search_term = st.text_input(
            "🔎 Search or filter extracted fields by name or value",
            placeholder="e.g. Patil, Income, 2026-2027, Caste...",
            label_visibility="collapsed"
        ).strip().lower()

        # Display Documents Cards
        for doc_type, extraction in extractions.items():
            doc_info = DOCUMENT_TYPES.get(doc_type, {})
            display_name = doc_info.get("display_name", doc_type)
            fields = extraction.get("extracted_fields", {})

            # Filter fields if search active
            if search_term:
                matched_fields = {
                    k: v for k, v in fields.items()
                    if search_term in k.lower() or (
                        search_term in str(v.get("value", "")).lower() if isinstance(v, dict) else search_term in str(v).lower()
                    )
                }
                if not matched_fields and search_term not in display_name.lower():
                    continue
            else:
                matched_fields = fields

            with st.expander(f"📄 {display_name} — {extraction.get('file_name', 'File')}", expanded=True):
                tab_fields, tab_raw = st.tabs(["📋 Structured Fields", "📝 Raw Extracted OCR Text"])

                with tab_fields:
                    if matched_fields:
                        st.markdown("""
                        <div style="display: grid; grid-template-columns: 2fr 3fr 1.5fr; font-size: 0.78rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; padding-bottom: 0.5rem; border-bottom: 1px solid #E2E8F0; margin-bottom: 0.75rem;">
                            <div>Field Name</div>
                            <div>Extracted Value (Editable)</div>
                            <div>Confidence Score</div>
                        </div>
                        """, unsafe_allow_html=True)

                        for field_name, field_data in matched_fields.items():
                            col_f1, col_f2, col_f3 = st.columns([2, 3, 1.5])

                            with col_f1:
                                is_confirmed = isinstance(field_data, dict) and field_data.get("is_user_confirmed", False)
                                badge_html = ' <span class="badge badge-review" style="font-size: 0.65rem;">EDITED</span>' if is_confirmed else ''
                                st.markdown(f"**{field_name.replace('_', ' ').title()}**{badge_html}", unsafe_allow_html=True)

                            with col_f2:
                                if isinstance(field_data, dict):
                                    value = field_data.get("value", "")
                                else:
                                    value = str(field_data)

                                new_value = st.text_input(
                                    f"val_{doc_type}_{field_name}",
                                    value=value,
                                    key=f"inp_{doc_type}_{field_name}",
                                    label_visibility="collapsed"
                                )

                                if new_value != value:
                                    if isinstance(field_data, dict):
                                        field_data["value"] = new_value
                                        field_data["is_user_confirmed"] = True
                                        field_data["confidence"] = 1.0
                                        field_data["original_value"] = value
                                    else:
                                        extraction["extracted_fields"][field_name] = {
                                            "value": new_value,
                                            "confidence": 1.0,
                                            "is_user_confirmed": True,
                                            "original_value": value,
                                        }

                            with col_f3:
                                if isinstance(field_data, dict):
                                    conf = field_data.get("confidence", 0.8)
                                    is_conf = field_data.get("is_user_confirmed", False)
                                    if is_conf:
                                        st.markdown("✅ **100%** (Verified)")
                                    else:
                                        bar_cls = "conf-high" if conf >= 0.8 else "conf-med" if conf >= 0.5 else "conf-low"
                                        st.markdown(f"""
                                        <div style="font-size: 0.82rem; font-weight: 600;">{conf:.0%}</div>
                                        <div class="conf-container">
                                            <div class="conf-bar {bar_cls}" style="width: {conf*100}%;"></div>
                                        </div>
                                        """, unsafe_allow_html=True)
                    else:
                        st.info("No matching structured fields found for this document.")

                with tab_raw:
                    raw_text = extraction.get("raw_text", "")
                    if raw_text:
                        st.caption(f"Raw character length: {len(raw_text)} chars • OCR Processing Time: {extraction.get('processing_time', 0):.2f}s")
                        st.text_area(
                            f"raw_text_{doc_type}",
                            value=raw_text[:6000],
                            height=220,
                            disabled=True,
                            label_visibility="collapsed"
                        )
                    else:
                        st.warning("No OCR text available for this file.")

    # ── Bottom Navigation ──
    st.markdown("---")
    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1.2])

    with nav_col1:
        if st.button("← Back to Upload", use_container_width=True):
            st.session_state.current_page = "upload"
            st.rerun()

    with nav_col3:
        can_proceed = bool(extractions)
        if st.button(
            "Run Verification ➡️",
            type="primary",
            use_container_width=True,
            disabled=not can_proceed,
        ):
            st.session_state.current_page = "verification"
            st.rerun()


def _run_extraction(uploaded_docs: dict):
    """Run OCR and field extraction on all uploaded documents."""
    progress_bar = st.progress(0, text="Initializing OCR engine...")
    extractions = {}
    total = len(uploaded_docs)

    for idx, (doc_type, doc_info) in enumerate(uploaded_docs.items()):
        doc_name = DOCUMENT_TYPES.get(doc_type, {}).get("display_name", doc_type)
        progress_bar.progress((idx) / total, text=f"Processing {doc_name} ({idx+1}/{total})...")

        file_path = doc_info.get("file_path", "")
        file_name = doc_info.get("file_name", "")

        start_time = time.time()

        try:
            # 1. OCR text extraction
            raw_text, ocr_confidence, ocr_warnings = extract_text_from_file(file_path)

            # 2. Structured field extraction
            fields, field_warnings = extract_fields_from_text(raw_text, doc_type)
            processing_time = time.time() - start_time

            extractions[doc_type] = {
                "document_type": doc_type,
                "file_name": file_name,
                "raw_text": raw_text,
                "extracted_fields": fields,
                "extraction_confidence": ocr_confidence,
                "processing_time": processing_time,
                "warnings": ocr_warnings + field_warnings,
                "errors": [],
            }
        except Exception as e:
            extractions[doc_type] = {
                "document_type": doc_type,
                "file_name": file_name,
                "raw_text": "",
                "extracted_fields": {},
                "extraction_confidence": 0.0,
                "processing_time": time.time() - start_time,
                "warnings": [],
                "errors": [f"Extraction failed: {str(e)}"],
            }

    progress_bar.progress(1.0, text="Extraction complete!")
    st.session_state.extractions = extractions
    st.session_state.total_docs_processed = st.session_state.get("total_docs_processed", 0) + len(extractions)
