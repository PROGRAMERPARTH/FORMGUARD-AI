"""
FORMGUARD AI - AI Assistant Page
AI-powered correction assistant with multilingual support and official MahaDBT RAG grounding.
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import SUPPORTED_LANGUAGES, GEMINI_API_KEY, DISCLAIMER, DOCUMENT_TYPES
from modules.ai_explainer import AIExplainer
from modules.rag_pipeline import RAGPipeline
from utils.ui_components import render_workflow_stepper


def render_assistant():
    """Render the AI correction assistant page."""
    # Render Workflow Stepper at top
    render_workflow_stepper("assistant")

    st.markdown("""
    <div class="formguard-header">
        <h1>🤖 AI Preflight Correction Assistant</h1>
        <div class="tagline">Trilingual AI guidance grounded in official MahaDBT guidelines, circulars, and FAQs</div>
    </div>
    """, unsafe_allow_html=True)

    verification_result = st.session_state.get("verification_result")
    extractions = st.session_state.get("extractions", {})
    language = st.session_state.get("language", "en")

    if not verification_result:
        st.warning("⚠️ No verification results available yet. Please run verification first.")
        if st.button("← Go to Verification", type="primary"):
            st.session_state.current_page = "verification"
            st.rerun()
        return

    # ── Interactive Language Switcher Bar ──
    st.markdown("**🌐 Select Guidance Language / भाषा निवडा:**")
    lang_c1, lang_c2, lang_c3, _ = st.columns([1, 1, 1, 2])
    
    with lang_c1:
        if st.button("🇬🇧 English", type="primary" if language == "en" else "secondary", use_container_width=True):
            st.session_state.language = "en"
            st.rerun()
    with lang_c2:
        if st.button("🇮🇳 हिन्दी", type="primary" if language == "hi" else "secondary", use_container_width=True):
            st.session_state.language = "hi"
            st.rerun()
    with lang_c3:
        if st.button("🇮🇳 मराठी", type="primary" if language == "mr" else "secondary", use_container_width=True):
            st.session_state.language = "mr"
            st.rerun()

    st.markdown("---")

    # ── Quick Issue Remediation Pills ──
    checks = verification_result.get("checks", [])
    issue_checks = [c for c in checks if c.get("severity") != "PASS"]

    if issue_checks:
        st.markdown("### ⚡ Click to Explain Detected Issues")
        st.caption("Select any flagged check below to automatically generate a step-by-step resolution plan:")

        # Render issue action cards
        for i, check in enumerate(issue_checks):
            severity = check.get("severity", "WARNING")
            icon = "🔴" if severity == "CRITICAL" else "🟡" if severity == "WARNING" else "🔵"

            col_issue, col_btn = st.columns([4, 1.2])
            with col_issue:
                st.markdown(f"""
                <div style="background: white; border-radius: 8px; padding: 0.65rem 1rem; border: 1px solid #E2E8F0; margin-bottom: 0.4rem;">
                    {icon} <strong>{check.get('check_name', 'Issue')}</strong>: <span style="color: #475569; font-size: 0.88rem;">{check.get('reason', '')}</span>
                </div>
                """, unsafe_allow_html=True)
            with col_btn:
                if st.button(f"Explain Issue 💡", key=f"explain_{i}", use_container_width=True):
                    _explain_issue_in_chat(check, st.session_state.language)
                    st.rerun()
    else:
        st.success("🎉 All verification checks passed! You can ask general questions about MahaDBT procedures below.")

    st.markdown("---")

    # ── Interactive Prompt Suggestions ──
    st.markdown("### 💬 Ask FORMGUARD AI")
    
    suggested_prompts = [
        "How do I fix a bank name initials mismatch?",
        "What is the income certificate validity on MahaDBT?",
        "Why is my college bonafide academic year flagged?",
        "How do I get an offline affidavit for a spelling error?",
    ]

    st.markdown("**Suggested questions for this application:**")
    p_cols = st.columns(len(suggested_prompts))
    for col, prompt in zip(p_cols, suggested_prompts):
        with col:
            if st.button(prompt, key=f"sug_{prompt[:18]}", use_container_width=True):
                _add_to_chat("user", prompt)
                _generate_response(prompt, verification_result, extractions, st.session_state.language)
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Chat Thread ──
    chat_history = st.session_state.get("chat_history", [])

    if chat_history:
        ch_head1, ch_head2 = st.columns([4, 1])
        with ch_head2:
            if st.button("🧹 Clear Chat History", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

    for msg in chat_history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        sources = msg.get("sources", [])

        if role == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(f"**Applicant:** {content}")
        else:
            with st.chat_message("assistant", avatar="🛡️"):
                st.markdown(content)
                if sources:
                    with st.expander("📚 Grounded Government Sources & Citations", expanded=False):
                        for src in sources:
                            st.markdown(f"- 🏛️ {src}")
                if msg.get("is_grounded"):
                    st.markdown('<span class="status-pill pill-success" style="font-size: 0.7rem;">✓ Grounded in MahaDBT Official Circulars</span>', unsafe_allow_html=True)

    # Chat Input
    user_input = st.chat_input("Type your question about MahaDBT scholarship requirements or corrections...")
    if user_input:
        _add_to_chat("user", user_input)
        _generate_response(user_input, verification_result, extractions, st.session_state.language)
        st.rerun()

    # Disclaimer
    st.markdown("---")
    st.caption(f"⚠️ {DISCLAIMER}")

    # ── Bottom Navigation ──
    st.markdown("<br>", unsafe_allow_html=True)
    col_back, col_spacer, col_report = st.columns([1, 2, 1.2])

    with col_back:
        if st.button("← Back to Verification", use_container_width=True):
            st.session_state.current_page = "verification"
            st.rerun()

    with col_report:
        if st.button("Generate Official Report ➡️", type="primary", use_container_width=True):
            st.session_state.current_page = "report"
            st.rerun()


def _add_to_chat(role: str, content: str, sources: list = None, is_grounded: bool = False):
    """Add a message to chat history."""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    st.session_state.chat_history.append({
        "role": role,
        "content": content,
        "sources": sources or [],
        "is_grounded": is_grounded,
    })


def _explain_issue_in_chat(check: dict, language: str):
    """Generate an AI explanation for a specific issue and add directly to chat."""
    explainer = AIExplainer()
    explanation = explainer.explain_check(check, language)

    question = f"How should I fix this issue: '{check.get('check_name')}'?"
    _add_to_chat("user", question)

    answer_text = explanation.get('explanation', '')
    if explanation.get('recommended_steps'):
        answer_text += "\n\n**Actionable Step-by-Step Resolution:**\n"
        for s in explanation['recommended_steps']:
            answer_text += f"1. {s}\n" if not s.startswith(("-", "1.", "2.", "3.")) else f"{s}\n"

    _add_to_chat(
        "assistant",
        answer_text,
        sources=explanation.get("sources", []),
        is_grounded=explanation.get("is_grounded", False),
    )


def _explain_issue(check: dict, language: str):
    """Generate an AI explanation for a specific issue."""
    explainer = AIExplainer()
    with st.spinner("🤖 Consulting MahaDBT Knowledge Base..."):
        explanation = explainer.explain_check(check, language)

    if explanation:
        st.markdown(f"""
        <div class="info-card">
            <strong>💡 AI Resolution Guidance</strong><br><br>
            {explanation.get('explanation', 'No explanation available.')}
        </div>
        """, unsafe_allow_html=True)

        if explanation.get("recommended_steps"):
            st.markdown("**Actionable Steps:**")
            for step in explanation["recommended_steps"]:
                st.markdown(f"- {step}")

        if explanation.get("sources"):
            with st.expander("📚 Citations & Government Circulars"):
                for src in explanation["sources"]:
                    st.markdown(f"- {src}")


def _generate_response(query: str, verification_result: dict, extractions: dict, language: str):
    """Generate a response using the AI assistant with RAG."""
    explainer = AIExplainer()
    context = _build_context(verification_result, extractions)
    response = explainer.answer_question(query, context, language)

    _add_to_chat(
        "assistant",
        response.get("answer", "I couldn't generate a response. Please refer to official guidelines."),
        sources=response.get("sources", []),
        is_grounded=response.get("is_grounded", False),
    )


def _build_context(verification_result: dict, extractions: dict) -> str:
    """Build context string from verification results for the AI."""
    context_parts = []
    context_parts.append(f"Scheme: {verification_result.get('scheme_name', 'Unknown')}")
    context_parts.append(f"Academic Year: {verification_result.get('academic_year', 'Unknown')}")
    context_parts.append(f"Category: {verification_result.get('applicant_category', 'Unknown')}")
    context_parts.append(f"Overall Readiness: {verification_result.get('overall_readiness', 0):.0f}%")
    context_parts.append("")

    context_parts.append("Verification Results:")
    for check in verification_result.get("checks", []):
        severity = check.get("severity", "PASS")
        context_parts.append(f"- [{severity}] {check.get('check_name', 'Check')}: {check.get('reason', '')}")
        if check.get("recommended_action"):
            context_parts.append(f"  Recommended: {check['recommended_action']}")
    context_parts.append("")

    context_parts.append("Extracted Document Information:")
    for doc_type, extraction in extractions.items():
        doc_name = DOCUMENT_TYPES.get(doc_type, {}).get("display_name", doc_type)
        context_parts.append(f"\n{doc_name}:")
        fields = extraction.get("extracted_fields", {})
        for field_name, field_data in fields.items():
            if isinstance(field_data, dict):
                value = field_data.get("value", "N/A")
            else:
                value = str(field_data)
            context_parts.append(f"  - {field_name}: {value}")

    return "\n".join(context_parts)
