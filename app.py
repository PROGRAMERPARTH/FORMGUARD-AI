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
        "scheme_id": "mahadbt_postmatric",
        "scheme_name": "MahaDBT Post-Matric Scholarship",
        "academic_year": "2026-2027",
        "applicant_category": "OBC",
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
        "remediation_status": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ── Import Pages & Config ──
from pages.dashboard import render_dashboard
from pages.upload import render_upload
from pages.document_intelligence import render_document_intelligence
from pages.verification import render_verification
from pages.assistant import render_assistant
from pages.report import render_report
from config import SUPPORTED_SCHEMES, DOCUMENT_TYPES, SUPPORTED_LANGUAGES

# ── Navigation Mapping ──
PAGES = {
    "landing": ("🏠", "Home"),
    "dashboard": ("📊", "Dashboard"),
    "upload": ("📤", "Upload Docs"),
    "extraction": ("🔍", "Document Intelligence"),
    "verification": ("✅", "Verification"),
    "assistant": ("🤖", "AI Assistant"),
    "report": ("📋", "Readiness Report"),
}


def navigate_to(page: str):
    """Navigate to a specific page."""
    st.session_state.current_page = page


# ── Sidebar ──
def render_sidebar():
    with st.sidebar:
        # Logo and branding
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0 0.5rem;">
            <div style="font-size: 2.2rem; margin-bottom: 0.25rem;">🛡️</div>
            <h2 style="color: white; margin: 0; font-size: 1.35rem; font-weight: 800; letter-spacing: -0.02em;">FORMGUARD AI</h2>
            <p style="color: #93C5FD; font-size: 0.78rem; margin-top: 0.25rem; font-weight: 500;">
                Detect Before You Submit
            </p>
        </div>
        <hr style="border-color: rgba(255,255,255,0.15); margin: 0.5rem 0 1rem;">
        """, unsafe_allow_html=True)

        # Navigation Header
        st.markdown('<p style="color: rgba(255,255,255,0.5); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.5rem; font-weight: 600;">Navigation</p>', unsafe_allow_html=True)

        # Nav items with dynamic badges
        for page_id, (icon, label) in PAGES.items():
            is_current = st.session_state.current_page == page_id
            
            # Badge logic
            badge = ""
            if page_id == "upload" and st.session_state.uploaded_documents:
                badge = f" ({len(st.session_state.uploaded_documents)})"
            elif page_id == "verification" and st.session_state.verification_result:
                v_res = st.session_state.verification_result
                issues = v_res.get("critical_count", 0) + v_res.get("warning_count", 0)
                badge = f" ({issues}⚠️)" if issues > 0 else " (✓)"

            btn_label = f"{icon} {label}{badge}"
            if st.button(
                btn_label,
                key=f"nav_{page_id}",
                use_container_width=True,
                type="primary" if is_current else "secondary",
            ):
                navigate_to(page_id)
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # Preflight Quick Status
        docs_count = len(st.session_state.uploaded_documents)
        has_verified = bool(st.session_state.verification_result)
        readiness = st.session_state.verification_result.get("overall_readiness", 0) if has_verified else 0

        st.markdown("""
        <div style="background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12); padding: 0.85rem; border-radius: 10px; margin-bottom: 1rem;">
            <div style="font-size: 0.72rem; color: rgba(255,255,255,0.6); text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">Pipeline Status</div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.4rem;">
                <span style="color: white; font-size: 0.82rem;">Uploaded Files</span>
                <span style="color: #6EE7B7; font-weight: 700; font-size: 0.82rem;">{docs_count}</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.25rem;">
                <span style="color: white; font-size: 0.82rem;">Readiness Score</span>
                <span style="color: {readiness_color}; font-weight: 700; font-size: 0.82rem;">{readiness_str}</span>
            </div>
        </div>
        """.format(
            docs_count=docs_count,
            readiness_str=f"{readiness:.0f}%" if has_verified else "Pending",
            readiness_color="#10B981" if readiness >= 80 else "#F59E0B" if readiness >= 50 else "#94A3B8"
        ), unsafe_allow_html=True)

        # Language selector
        st.markdown('<p style="color: rgba(255,255,255,0.5); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.4rem; font-weight: 600;">Language / भाषा</p>', unsafe_allow_html=True)
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
            st.rerun()

        # Hackathon metadata
        st.markdown("""
        <div style="margin-top: 1.5rem; padding: 0.75rem; background: rgba(0,0,0,0.25); border-radius: 8px;">
            <div style="color: #60A5FA; font-size: 0.72rem; font-weight: 700;">IDEA//FORGE Hackathon</div>
            <div style="color: rgba(255,255,255,0.7); font-size: 0.68rem; margin-top: 2px;">Track 1: Civic Pulse & Digital Governance</div>
            <div style="color: rgba(255,255,255,0.4); font-size: 0.65rem; margin-top: 4px;">v1.2.0 • Offline RAG & OCR Ready</div>
        </div>
        """, unsafe_allow_html=True)


# ── Landing Page ──
def render_landing():
    """Render the landing page."""
    # Hero Section
    st.markdown("""
    <div class="hero-section">
        <div class="hero-badge">🏛️ Civic Pulse • Digital Governance & Public Information</div>
        <div class="hero-title">FORMGUARD AI</div>
        <div class="hero-tagline">Intelligent Government Application Preflight Verification System</div>
        <p class="hero-desc">
            Stop scholarship rejection before it happens. Detect cross-document name mismatches, missing certificates,
            and academic year inconsistencies with deterministic verification and government-rule-grounded RAG.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Interactive Action Bar
    act_col1, act_col2, act_col3 = st.columns([2, 2, 1.5])
    with act_col1:
        if st.button("🚀 Start Application Verification", type="primary", use_container_width=True):
            navigate_to("upload")
            st.rerun()
    with act_col2:
        if st.button("⚡ Live Demo: Load Synthetic Case (1-Click)", type="secondary", use_container_width=True, help="Load synthetic student documents for instant evaluation"):
            from modules.demo_generator import generate_all_demo_documents
            from config import TEMP_DIR
            demo_docs = generate_all_demo_documents(str(TEMP_DIR))
            st.session_state.uploaded_documents = demo_docs
            st.session_state.scheme_id = "mahadbt_postmatric"
            st.session_state.scheme_name = "MahaDBT Post-Matric Scholarship"
            st.session_state.academic_year = "2026-2027"
            st.session_state.applicant_category = "OBC"
            st.success("✅ Synthetic demo case loaded (5 documents)! Proceeding to Extraction...")
            navigate_to("extraction")
            st.rerun()
    with act_col3:
        if st.button("📊 View Dashboard", use_container_width=True):
            navigate_to("dashboard")
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Live Preflight Stepper Overview ──
    st.markdown("### ⚙️ How Preflight Verification Works")
    step_cols = st.columns(4)
    flow_steps = [
        ("1️⃣", "Select & Upload", "Choose Maharashtra welfare scheme (MahaDBT) and upload certificates."),
        ("2️⃣", "OCR Extraction", "PyMuPDF & Tesseract extract text, names, dates, and certificate numbers."),
        ("3️⃣", "Cross-Verification", "Deterministic engine cross-checks initials, income caps, and academic years."),
        ("4️⃣", "RAG & Action Report", "Official circulars ground the AI explainer and generate a readiness PDF."),
    ]
    for col, (num, title, desc) in zip(step_cols, flow_steps):
        with col:
            st.markdown(f"""
            <div class="metric-card" style="border-top: 3px solid #2E5090;">
                <div style="font-size: 1.4rem; margin-bottom: 0.35rem;">{num}</div>
                <div style="font-size: 0.95rem; font-weight: 700; color: #1B2A4A; margin-bottom: 0.35rem;">{title}</div>
                <div style="font-size: 0.82rem; color: #64748B; line-height: 1.4;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Interactive Scheme Requirements Inspector ──
    st.markdown("### 📋 Interactive Scheme Requirement Explorer")
    st.caption("Inspect official MahaDBT requirements before uploading your documents.")

    scheme_keys = list(SUPPORTED_SCHEMES.keys())
    selected_scheme_key = st.selectbox(
        "Choose Government Scheme to inspect:",
        options=scheme_keys,
        format_func=lambda k: SUPPORTED_SCHEMES[k]["name"],
        label_visibility="collapsed"
    )

    scheme_info = SUPPORTED_SCHEMES[selected_scheme_key]
    ins_col1, ins_col2 = st.columns([1.5, 2])
    with ins_col1:
        st.markdown(f"""
        <div class="info-card">
            <h4 style="margin: 0 0 0.5rem; color: #1B2A4A;">{scheme_info['name']}</h4>
            <p style="font-size: 0.85rem; color: #64748B; margin-bottom: 0.75rem;">{scheme_info['description']}</p>
            <p style="font-size: 0.82rem; margin: 0;"><strong>Income Limit:</strong> ₹8,00,000 / year (OBC/EBC)</p>
            <p style="font-size: 0.82rem; margin: 0.2rem 0 0;"><strong>Eligible Years:</strong> {', '.join(scheme_info.get('academic_years', []))}</p>
            <div style="margin-top: 0.75rem;">
                <a href="{scheme_info.get('source_url', '#')}" target="_blank" style="font-size: 0.8rem; font-weight: 600; color: #2E5090;">🔗 Official MahaDBT Portal ↗</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with ins_col2:
        st.markdown("**Required & Optional Documents for this Scheme:**")
        req_d = scheme_info.get("required_documents", [])
        opt_d = scheme_info.get("optional_documents", [])

        req_cols = st.columns(2)
        with req_cols[0]:
            st.markdown("*Mandatory Checklist:*")
            for doc in req_d:
                d_name = DOCUMENT_TYPES.get(doc, {}).get("display_name", doc)
                st.markdown(f"🔴 **{d_name}**")
        with req_cols[1]:
            st.markdown("*Supporting / Optional:*")
            for doc in opt_d:
                d_name = DOCUMENT_TYPES.get(doc, {}).get("display_name", doc)
                st.markdown(f"🔵 {d_name}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Core Features Grid ──
    st.markdown("### ✨ Why FORMGUARD AI?")
    f_col1, f_col2, f_col3 = st.columns(3)
    features = [
        ("🔀", "Cross-Document Verification", "Pinpoint name variations (e.g. initials 'R. S. Patil' vs full name) and mismatched fathers' names before submission."),
        ("📚", "Grounded MahaDBT RAG", "Answers and validations cite official Maharashtra Government Resolutions and MahaDBT portal FAQs with real source URLs."),
        ("📅", "Academic Year Validation", "Ensure bonafide certificate matches the current scholarship year while accepting prior qualifying exam marksheets."),
        ("🌐", "Trilingual Assistant", "Instant clarification in English, Marathi (मराठी) and Hindi (हिन्दी) tailored for Indian applicants."),
        ("🔒", "Client-Side Privacy First", "Aadhaar number masking, bank account protection, and in-memory temporary session handling."),
        ("📋", "Auditable PDF Reports", "Generate an official-grade Preflight Verification Report with full audit trail and correction checklist."),
    ]
    for i, (icon, title, desc) in enumerate(features):
        with [f_col1, f_col2, f_col3][i % 3]:
            st.markdown(f"""
            <div class="modern-card" style="margin-bottom: 1rem;">
                <div class="card-icon">{icon}</div>
                <h4 style="margin: 0.75rem 0 0.35rem; color: #1B2A4A; font-size: 1rem;">{title}</h4>
                <p style="color: #64748B; font-size: 0.85rem; line-height: 1.45; margin: 0;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Live System Verification Status Banner ──
    st.markdown("""
    <div style="background: #F1F5F9; border-radius: 12px; padding: 1.25rem 1.75rem; border: 1px solid #E2E8F0; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
        <div>
            <strong style="color: #1E293B; font-size: 0.95rem;">System Health & Knowledge Base Status</strong>
            <div style="color: #64748B; font-size: 0.82rem; margin-top: 0.2rem;">All engines operating deterministically with offline backup fallbacks.</div>
        </div>
        <div style="display: flex; gap: 0.75rem; flex-wrap: wrap;">
            <span class="status-pill pill-success">✓ PyMuPDF OCR: Active</span>
            <span class="status-pill pill-success">✓ FAISS Index: 8 Chunks Loaded</span>
            <span class="status-pill pill-info">✓ Trilingual Engine: Ready</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Disclaimer & Footer
    st.markdown("---")
    st.caption(
        "⚠️ **Disclaimer**: FORMGUARD AI provides preflight application verification assistance. "
        "It is not an official government verification, eligibility decision, or guarantee of application approval. "
        "Always verify with official government portals at mahadbt.maharashtra.gov.in."
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
