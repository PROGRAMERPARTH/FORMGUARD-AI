"""
FORMGUARD AI - AI Assistant Page
AI-powered correction assistant with multilingual support and RAG.
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import SUPPORTED_LANGUAGES, GEMINI_API_KEY, DISCLAIMER, DOCUMENT_TYPES
from modules.ai_explainer import AIExplainer
from modules.rag_pipeline import RAGPipeline


def render_assistant():
    """Render the AI correction assistant page."""
    st.markdown("""
    <div class="formguard-header">
        <h1>🤖 AI Correction Assistant</h1>
        <div class="tagline">Get AI-powered explanations and corrections grounded in official guidelines</div>
    </div>
    """, unsafe_allow_html=True)

    verification_result = st.session_state.get("verification_result")
    extractions = st.session_state.get("extractions", {})
    language = st.session_state.get("language", "en")

    if not verification_result:
        st.warning("⚠️ No verification results available. Please run verification first.")
        if st.button("← Go to Verification"):
            st.session_state.current_page = "verification"
            st.rerun()
        return

    # ── Language Selection ──
    col_lang, col_spacer = st.columns([1, 3])
    with col_lang:
        lang_options = {k: v for k, v in SUPPORTED_LANGUAGES.items()}
        selected_lang = st.selectbox(
            "🌐 Response Language",
            options=list(lang_options.keys()),
            format_func=lambda x: lang_options[x],
            index=list(lang_options.keys()).index(language),
        )
        if selected_lang != language:
            st.session_state.language = selected_lang
            language = selected_lang

    st.markdown("---")

    # ── Issue Summary for Quick Actions ──
    checks = verification_result.get("checks", [])
    issue_checks = [c for c in checks if c.get("severity") != "PASS"]

    if issue_checks:
        st.markdown("### ⚡ Quick Issue Explanations")
        st.caption("Click on any issue below to get an AI-powered explanation.")

        for i, check in enumerate(issue_checks):
            severity = check.get("severity", "WARNING")
            icon = "🔴" if severity == "CRITICAL" else "🟡" if severity == "WARNING" else "🔵"

            col_issue, col_btn = st.columns([4, 1])
            with col_issue:
                st.markdown(f"{icon} **{check.get('check_name', 'Issue')}**: {check.get('reason', '')}")
            with col_btn:
                if st.button("Explain", key=f"explain_{i}", use_container_width=True):
                    _explain_issue_in_chat(check, language)
                    st.rerun()
    else:
        st.success("✅ All verification checks passed! No issues to explain.")

    st.markdown("---")

    # ── Chat Interface ──
    st.markdown("### 💬 Ask the Assistant")
    st.caption("Ask questions about your verification results, scheme requirements, or document corrections.")

    # Suggested questions
    suggested = [
        "Why is my name showing a mismatch?",
        "Which documents are missing?",
        "What is the income limit for this scheme?",
        "How can I correct my documents?",
        "What does this government requirement mean?",
    ]

    st.markdown("**Suggested questions:**")
    suggestion_cols = st.columns(len(suggested))
    for col, q in zip(suggestion_cols, suggested):
        with col:
            if st.button(q, key=f"suggest_{q[:20]}", use_container_width=True):
                _add_to_chat("user", q)
                _generate_response(q, verification_result, extractions, language)
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Chat history
    chat_history = st.session_state.get("chat_history", [])
    for msg in chat_history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        sources = msg.get("sources", [])

        if role == "user":
            st.chat_message("user").markdown(content)
        else:
            with st.chat_message("assistant"):
                st.markdown(content)
                if sources:
                    with st.expander("📚 Sources"):
                        for src in sources:
                            st.markdown(f"- {src}")
                if msg.get("is_grounded"):
                    st.caption("✅ Response grounded in official scheme guidelines")
                else:
                    st.caption("ℹ️ General recommendation — verify with official sources")

    # Chat input
    user_input = st.chat_input("Ask about your verification results...")
    if user_input:
        _add_to_chat("user", user_input)
        _generate_response(user_input, verification_result, extractions, language)
        st.rerun()

    # Disclaimer
    st.markdown("---")
    st.caption(f"⚠️ {DISCLAIMER}")

    # ── Navigation ──
    st.markdown("<br>", unsafe_allow_html=True)
    col_back, col_spacer, col_report = st.columns([1, 2, 1])

    with col_back:
        if st.button("← Back to Verification", use_container_width=True):
            st.session_state.current_page = "verification"
            st.rerun()

    with col_report:
        if st.button("📋 Generate Report →", type="primary", use_container_width=True):
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
    
    question = f"Why did check '{check.get('check_name')}' flag an issue?"
    _add_to_chat("user", question)
    
    answer_text = explanation.get('explanation', '')
    if explanation.get('recommended_steps'):
        answer_text += "\n\n**Recommended Next Actions:**\n"
        for s in explanation['recommended_steps']:
            answer_text += f"- {s}\n"
            
    _add_to_chat(
        "assistant",
        answer_text,
        sources=explanation.get("sources", []),
        is_grounded=explanation.get("is_grounded", False),
    )


def _explain_issue(check: dict, language: str):
    """Generate an AI explanation for a specific issue."""
    explainer = AIExplainer()

    with st.spinner("🤖 Generating explanation..."):
        explanation = explainer.explain_check(check, language)

    if explanation:
        st.markdown(f"""
        <div class="info-card">
            <strong>💡 AI Explanation</strong><br><br>
            {explanation.get('explanation', 'No explanation available.')}
        </div>
        """, unsafe_allow_html=True)

        if explanation.get("recommended_steps"):
            st.markdown("**Recommended Steps:**")
            for step in explanation["recommended_steps"]:
                st.markdown(f"  {step}")

        if explanation.get("sources"):
            with st.expander("📚 Sources"):
                for src in explanation["sources"]:
                    st.markdown(f"- {src}")
    else:
        st.info("Could not generate an AI explanation. Please refer to official scheme guidelines for guidance.")


def _generate_response(query: str, verification_result: dict, extractions: dict, language: str):
    """Generate a response using the AI assistant with RAG."""
    explainer = AIExplainer()

    # Build context from verification results
    context = _build_context(verification_result, extractions)

    response = explainer.answer_question(query, context, language)

    _add_to_chat(
        "assistant",
        response.get("answer", "I'm sorry, I couldn't generate a response. Please try again or refer to official guidelines."),
        sources=response.get("sources", []),
        is_grounded=response.get("is_grounded", False),
    )


def _build_context(verification_result: dict, extractions: dict) -> str:
    """Build context string from verification results for the AI."""
    context_parts = []

    # Add scheme info
    context_parts.append(f"Scheme: {verification_result.get('scheme_name', 'Unknown')}")
    context_parts.append(f"Academic Year: {verification_result.get('academic_year', 'Unknown')}")
    context_parts.append(f"Category: {verification_result.get('applicant_category', 'Unknown')}")
    context_parts.append(f"Overall Readiness: {verification_result.get('overall_readiness', 0):.0f}%")
    context_parts.append("")

    # Add verification results
    context_parts.append("Verification Results:")
    for check in verification_result.get("checks", []):
        severity = check.get("severity", "PASS")
        context_parts.append(f"- [{severity}] {check.get('check_name', 'Check')}: {check.get('reason', '')}")
        if check.get("recommended_action"):
            context_parts.append(f"  Recommended: {check['recommended_action']}")
    context_parts.append("")

    # Add extraction summaries
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
