"""
FORMGUARD AI - Main Application Entry Point
Intelligent Government Application Preflight Verification System

"Detect Before You Submit."

Run: streamlit run app.py
"""

import streamlit as st
import os
from pathlib import Path

# ── Page Configuration ──
st.set_page_config(
    page_title="FORMGUARD AI - Detect Before You Submit",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "FORMGUARD AI - Intelligent Government Application Preflight Verification System. Built for IDEA//FORGE Hackathon."
    }
)

# ── Load Custom CSS ──
def load_css():
    css_path = Path(__file__).parent / "assets" / "styles.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ── Initialize Session State ──
def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        "current_page": "landing",
        "session_id": None,
        "scheme_id": None,
        "scheme_name": None,
        "academic_year": None,
        "applicant_category": None,
        "uploaded_documents": {},
        "extractions": {},
        "verification_result": None,
        "verification_report": None,
        "chat_history": [],
        "language": "en",
        "sessions_history": [],
        "total_docs_processed": 0,
        "total_issues_found": 0,
        "total_reports_generated": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ── Import Pages ──
from pages.dashboard import render_dashboard
from pages.upload import render_upload
from pages.document_intelligence import render_document_intelligence
from pages.verification import render_verification
from pages.assistant import render_assistant
from pages.report import render_report

# ── Navigation Mapping ──
PAGES = {
    "landing": "🏠 Home",
    "dashboard": "📊 Dashboard",
    "upload": "📤 Upload Documents",
    "extraction": "🔍 Document Intelligence",
    "verification": "✅ Verification",
    "assistant": "🤖 AI Assistant",
    "report": "📋 Report",
}


def navigate_to(page: str):
    """Navigate to a specific page."""
    st.session_state.current_page = page


# ── Sidebar ──
def render_sidebar():
    with st.sidebar:
        # Logo and branding
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h2 style="color: white; margin: 0;">🛡️ FORMGUARD AI</h2>
            <p style="color: rgba(255,255,255,0.7); font-size: 0.8rem; margin-top: 0.25rem;">
                Detect Before You Submit
            </p>
        </div>
        <hr style="border-color: rgba(255,255,255,0.2); margin: 0.5rem 0 1rem;">
        """, unsafe_allow_html=True)

        # Navigation
        st.markdown('<p style="color: rgba(255,255,255,0.6); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em;">Navigation</p>', unsafe_allow_html=True)

        for page_id, page_name in PAGES.items():
            is_current = st.session_state.current_page == page_id
            if st.button(
                page_name,
                key=f"nav_{page_id}",
                use_container_width=True,
                type="primary" if is_current else "secondary",
            ):
                navigate_to(page_id)
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # Language selector
        st.markdown('<p style="color: rgba(255,255,255,0.6); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em;">Language</p>', unsafe_allow_html=True)
        languages = {"en": "🇬🇧 English", "hi": "🇮🇳 हिन्दी", "mr": "🇮🇳 मराठी"}
        selected_lang = st.selectbox(
            "Response Language",
            options=list(languages.keys()),
            format_func=lambda x: languages[x],
            index=list(languages.keys()).index(st.session_state.language),
            label_visibility="collapsed",
        )
        if selected_lang != st.session_state.language:
            st.session_state.language = selected_lang

        st.markdown("<br>", unsafe_allow_html=True)

        # Session info
        if st.session_state.session_id:
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.1); padding: 0.75rem; border-radius: 8px; font-size: 0.8rem;">
                <p style="color: rgba(255,255,255,0.6); margin: 0;">Active Session</p>
                <p style="color: white; margin: 0.25rem 0 0; font-family: monospace; font-size: 0.7rem;">{st.session_state.session_id[:16]}...</p>
            </div>
            """, unsafe_allow_html=True)

        # Footer
        st.markdown("""
        <div style="position: fixed; bottom: 1rem; padding-right: 1rem;">
            <p style="color: rgba(255,255,255,0.4); font-size: 0.65rem; margin: 0;">
                FORMGUARD AI v1.0.0<br>
                IDEA//FORGE Hackathon<br>
                Track 1: Civic Pulse
            </p>
        </div>
        """, unsafe_allow_html=True)


# ── Landing Page ──
def render_landing():
    """Render the landing page."""
    # Hero Section
    st.markdown("""
    <div class="hero-section">
        <div class="hero-title">🛡️ FORMGUARD AI</div>
        <div class="hero-tagline">Intelligent Government Application Preflight Verification System</div>
        <p style="font-size: 1.5rem; font-weight: 300; opacity: 0.95; position: relative;">
            Detect Before You Submit.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Problem Statement
    st.markdown("### 🎯 The Problem")
    st.markdown("""
    Every year, thousands of students in Maharashtra face **scholarship application delays and rejections** due to:
    - ❌ Inconsistent names across certificates
    - ❌ Missing mandatory documents
    - ❌ Incorrect academic year information
    - ❌ Invalid or expired certificates
    - ❌ Mismatched personal details across forms

    **These are preventable errors.** FORMGUARD AI helps you catch them *before* you submit.
    """)

    st.markdown("---")

    # How It Works
    st.markdown("### ⚙️ How It Works")
    cols = st.columns(4)
    steps = [
        ("📋", "Select Scheme", "Choose your government scholarship scheme and academic year."),
        ("📤", "Upload Documents", "Upload your certificates, marksheets, and supporting documents."),
        ("🔍", "AI Verification", "Our AI extracts, compares, and verifies information across all documents."),
        ("📊", "Get Report", "Receive a detailed readiness report with corrections and recommendations."),
    ]
    for col, (icon, title, desc) in zip(cols, steps):
        with col:
            st.markdown(f"""
            <div class="feature-card">
                <div class="feature-icon">{icon}</div>
                <div class="feature-title">{title}</div>
                <div class="feature-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Features
    st.markdown("### ✨ Key Features")
    col1, col2, col3 = st.columns(3)
    features = [
        ("🔎", "Smart OCR Extraction", "Extract text from PDFs and images with intelligent field recognition."),
        ("🔄", "Cross-Document Verification", "Automatically compare names, dates, and details across all your certificates."),
        ("📚", "Government Rule-Aware RAG", "AI grounded in official MahaDBT scheme requirements and guidelines."),
        ("💡", "AI Explanations", "Clear, actionable explanations for every detected issue."),
        ("🌐", "Multilingual Support", "Get assistance in English, Hindi, and Marathi."),
        ("📄", "PDF Reports", "Download detailed verification reports for your records."),
    ]
    for i, (icon, title, desc) in enumerate(features):
        with [col1, col2, col3][i % 3]:
            st.markdown(f"""
            <div class="feature-card" style="margin-bottom: 1rem;">
                <div class="feature-icon">{icon}</div>
                <div class="feature-title">{title}</div>
                <div class="feature-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Supported Documents
    st.markdown("### 📎 Supported Documents")
    doc_cols = st.columns(4)
    doc_types = [
        "📜 Income Certificate", "📜 Caste Certificate",
        "📜 Domicile Certificate", "🏫 College Bonafide",
        "📝 Academic Marksheet", "🏦 Bank Passbook/Cheque",
        "🪪 Aadhaar Card", "📄 Other Certificates",
    ]
    for i, doc in enumerate(doc_types):
        with doc_cols[i % 4]:
            st.markdown(f"✅ {doc}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Supported Languages
    st.markdown("### 🌐 Supported Languages")
    lang_cols = st.columns(3)
    with lang_cols[0]:
        st.markdown("🇬🇧 **English**")
    with lang_cols[1]:
        st.markdown("🇮🇳 **हिन्दी (Hindi)**")
    with lang_cols[2]:
        st.markdown("🇮🇳 **मराठी (Marathi)**")

    st.markdown("<br>", unsafe_allow_html=True)

    # CTA
    col_left, col_btn1, col_btn2, col_right = st.columns([1, 2, 2, 1])
    with col_btn1:
        if st.button("🚀 Start Application Verification", type="primary", use_container_width=True):
            navigate_to("upload")
            st.rerun()
    with col_btn2:
        if st.button("⚡ Live Demo: Load Sample Case", type="secondary", use_container_width=True, help="Load synthetic student documents for instant evaluation"):
            from modules.demo_generator import generate_all_demo_documents
            from config import TEMP_DIR
            demo_docs = generate_all_demo_documents(str(TEMP_DIR))
            st.session_state.uploaded_documents = demo_docs
            st.session_state.scheme_id = "mahadbt_postmatric"
            st.session_state.scheme_name = "MahaDBT Post-Matric Scholarship"
            st.session_state.academic_year = "2026-2027"
            st.session_state.applicant_category = "OBC"
            navigate_to("extraction")
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Privacy & Security
    st.markdown("### 🔒 Privacy & Security")
    st.info("""
    - **No permanent storage**: Your documents are processed temporarily and deleted after verification.
    - **Sensitive data masking**: Aadhaar and bank account numbers are automatically masked.
    - **Local processing**: Document analysis runs on-device where possible.
    - **No sharing**: Your documents are never shared with third parties.
    """)

    # Disclaimer
    st.markdown("---")
    st.caption(
        "⚠️ **Disclaimer**: FORMGUARD AI provides AI-assisted document consistency and scheme-requirement checks. "
        "It is not an official government verification, eligibility decision, or guarantee of application approval. "
        "Always verify with official government portals and authorities."
    )
    st.caption("Built for **IDEA//FORGE Online Hackathon** | Track 1: Civic Pulse, Digital Governance & Public Information")


# ── Main App Router ──
def main():
    render_sidebar()

    page = st.session_state.current_page

    if page == "landing":
        render_landing()
    elif page == "dashboard":
        render_dashboard()
    elif page == "upload":
        render_upload()
    elif page == "extraction":
        render_document_intelligence()
    elif page == "verification":
        render_verification()
    elif page == "assistant":
        render_assistant()
    elif page == "report":
        render_report()
    else:
        render_landing()


if __name__ == "__main__":
    main()
