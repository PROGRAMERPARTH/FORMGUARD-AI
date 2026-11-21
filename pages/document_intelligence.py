"""
FORMGUARD AI - Document Intelligence Page
OCR extraction and structured field display with user review.
"""

import streamlit as st
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DOCUMENT_TYPES
from modules.ocr_engine import extract_text_from_file
from modules.field_extractor import extract_fields_from_text


def render_document_intelligence():
    """Render the document intelligence / OCR extraction page."""
    st.markdown("""
    <div class="formguard-header">
        <h1>🔍 Document Intelligence</h1>
        <div class="tagline">AI-powered text extraction and field recognition</div>
    </div>
    """, unsafe_allow_html=True)

    uploaded_docs = st.session_state.get("uploaded_documents", {})

    if not uploaded_docs:
        st.warning("⚠️ No documents uploaded. Please go to the Upload page first.")
        if st.button("← Go to Upload"):
            st.session_state.current_page = "upload"
            st.rerun()
        return

    # ── Run Extraction Button ──
    extractions = st.session_state.get("extractions", {})

    if not extractions:
        st.markdown("""
        <div class="info-card">
            <strong>📄 Ready to Extract</strong><br>
            Click below to run OCR and AI extraction on your uploaded documents.
            This will extract text and identify key fields from each document.
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔍 Extract Document Information", type="primary", use_container_width=True):
            _run_extraction(uploaded_docs)
            st.rerun()
    else:
        # Show re-run option
        if st.button("🔄 Re-run Extraction", help="Re-extract text from all documents"):
            st.session_state.extractions = {}
            _run_extraction(uploaded_docs)
            st.rerun()

    # ── Display Extractions ──
    if extractions:
        st.markdown("---")
        st.markdown("### 📋 Extracted Information")
        st.caption("Review the extracted fields below. You can correct any mistakes before verification.")

        # Summary metrics
        total_fields = sum(len(ext.get("extracted_fields", {})) for ext in extractions.values())
        avg_confidence = 0
        confidence_values = []
        for ext in extractions.values():
            for field_data in ext.get("extracted_fields", {}).values():
                if isinstance(field_data, dict) and "confidence" in field_data:
                    confidence_values.append(field_data["confidence"])
        if confidence_values:
            avg_confidence = sum(confidence_values) / len(confidence_values)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Documents Processed", len(extractions))
        with col2:
            st.metric("Fields Extracted", total_fields)
        with col3:
            st.metric("Avg. Confidence", f"{avg_confidence:.0%}")

        st.markdown("<br>", unsafe_allow_html=True)

        # Display each document's extraction
        for doc_type, extraction in extractions.items():
            doc_info = DOCUMENT_TYPES.get(doc_type, {})
            display_name = doc_info.get("display_name", doc_type)

            with st.expander(f"📄 {display_name} — {extraction.get('file_name', 'Unknown')}", expanded=True):
                tab_fields, tab_raw = st.tabs(["📋 Extracted Fields", "📝 Raw Text"])

                with tab_fields:
                    fields = extraction.get("extracted_fields", {})
                    if fields:
                        # Create editable field display
                        for field_name, field_data in fields.items():
                            col_label, col_value, col_conf = st.columns([2, 3, 1])

                            with col_label:
                                st.markdown(f"**{field_name.replace('_', ' ').title()}**")

                            with col_value:
                                if isinstance(field_data, dict):
                                    value = field_data.get("value", "")
                                    confidence = field_data.get("confidence", 0)
                                else:
                                    value = str(field_data)
                                    confidence = 0.5

                                # Editable field
                                new_value = st.text_input(
                                    f"Value for {field_name}",
                                    value=value,
                                    key=f"edit_{doc_type}_{field_name}",
                                    label_visibility="collapsed",
                                )

                                # Track if user confirmed/edited
                                if new_value != value:
                                    if isinstance(field_data, dict):
                                        field_data["value"] = new_value
                                        field_data["is_user_confirmed"] = True
                                        field_data["original_value"] = value
                                    else:
                                        extraction["extracted_fields"][field_name] = {
                                            "value": new_value,
                                            "confidence": 1.0,
                                            "is_user_confirmed": True,
                                            "original_value": value,
                                        }

                            with col_conf:
                                if isinstance(field_data, dict):
                                    conf = field_data.get("confidence", 0)
                                    is_confirmed = field_data.get("is_user_confirmed", False)
                                    if is_confirmed:
                                        st.markdown("✅ Confirmed")
                                    elif conf >= 0.8:
                                        st.markdown(f"🟢 {conf:.0%}")
                                    elif conf >= 0.5:
                                        st.markdown(f"🟡 {conf:.0%}")
                                    else:
                                        st.markdown(f"🔴 {conf:.0%}")
                    else:
                        st.info("No structured fields could be extracted from this document.")

                with tab_raw:
                    raw_text = extraction.get("raw_text", "")
                    if raw_text:
                        st.text_area(
                            "Extracted Text",
                            value=raw_text[:5000],  # Limit display
                            height=300,
                            disabled=True,
                            key=f"raw_{doc_type}",
                        )
                        if len(raw_text) > 5000:
                            st.caption(f"Showing first 5000 of {len(raw_text)} characters.")
                    else:
                        st.warning("No text could be extracted from this document.")

                # Warnings and errors
                warnings = extraction.get("warnings", [])
                errors = extraction.get("errors", [])
                if warnings:
                    for w in warnings:
                        st.warning(f"⚠️ {w}")
                if errors:
                    for e in errors:
                        st.error(f"❌ {e}")

    # ── Navigation ──
    st.markdown("---")
    col_back, col_spacer, col_next = st.columns([1, 2, 1])

    with col_back:
        if st.button("← Back to Upload", use_container_width=True):
            st.session_state.current_page = "upload"
            st.rerun()

    with col_next:
        can_proceed = bool(st.session_state.get("extractions"))
        if st.button(
            "Run Verification →",
            type="primary",
            use_container_width=True,
            disabled=not can_proceed,
        ):
            st.session_state.current_page = "verification"
            st.rerun()

        if not can_proceed:
            st.caption("Extract document data first to proceed.")


def _run_extraction(uploaded_docs: dict):
    """Run OCR and field extraction on all uploaded documents."""
    progress_bar = st.progress(0, text="Preparing extraction...")
    extractions = {}
    total = len(uploaded_docs)

    for idx, (doc_type, doc_info) in enumerate(uploaded_docs.items()):
        progress_text = f"Processing {DOCUMENT_TYPES.get(doc_type, {}).get('display_name', doc_type)}..."
        progress_bar.progress((idx) / total, text=progress_text)

        file_path = doc_info.get("file_path", "")
        file_name = doc_info.get("file_name", "")

        start_time = time.time()

        try:
            # Step 1: OCR / Text extraction
            raw_text, ocr_confidence, ocr_warnings = extract_text_from_file(file_path)

            # Step 2: Structured field extraction
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

    # Update total docs processed
    st.session_state.total_docs_processed = st.session_state.get("total_docs_processed", 0) + len(extractions)
