"""
FORMGUARD AI - Reusable UI Components
Modern, interactive UI components for Streamlit.
"""

import streamlit as st


def render_workflow_stepper(current_step: str):
    """
    Renders an interactive, visually stunning horizontal workflow stepper.
    Steps:
      1. upload: Select & Upload
      2. extraction: OCR Intelligence
      3. verification: Cross-Verification
      4. assistant: AI Assistant
      5. report: Verification Report
    """
    steps = [
        {"id": "upload", "num": "1", "icon": "📤", "label": "Upload", "title": "Scheme & Docs"},
        {"id": "extraction", "num": "2", "icon": "🔍", "label": "OCR Extract", "title": "Field Intelligence"},
        {"id": "verification", "num": "3", "icon": "✅", "label": "Verify", "title": "Cross-Validation"},
        {"id": "assistant", "num": "4", "icon": "🤖", "label": "AI Explain", "title": "Correction Assistant"},
        {"id": "report", "num": "5", "icon": "📋", "label": "Report", "title": "Readiness PDF"},
    ]

    has_docs = bool(st.session_state.get("uploaded_documents"))
    has_extractions = bool(st.session_state.get("extractions"))
    has_verification = bool(st.session_state.get("verification_result"))

    step_status = {
        "upload": "completed" if has_docs else ("current" if current_step == "upload" else "pending"),
        "extraction": "completed" if has_extractions else ("current" if current_step == "extraction" else ("ready" if has_docs else "disabled")),
        "verification": "completed" if has_verification else ("current" if current_step == "verification" else ("ready" if has_extractions else "disabled")),
        "assistant": "ready" if has_verification else ("current" if current_step == "assistant" else "disabled"),
        "report": "ready" if has_verification else ("current" if current_step == "report" else "disabled"),
    }

    stepper_html = ['<div class="stepper-container">']

    for i, s in enumerate(steps):
        sid = s["id"]
        is_active = (current_step == sid)
        status = step_status.get(sid, "pending")
        
        # Determine CSS class
        item_class = "stepper-step"
        if is_active:
            item_class += " active"
        elif status == "completed":
            item_class += " completed"
        elif status == "ready":
            item_class += " ready"
        else:
            item_class += " disabled"

        # Badge content
        badge_content = "✓" if (status == "completed" and not is_active) else s["num"]

        stepper_html.append(f"""
        <div class="{item_class}">
            <div class="step-circle">{badge_content}</div>
            <div class="step-text">
                <span class="step-title">{s['icon']} {s['label']}</span>
                <span class="step-sub">{s['title']}</span>
            </div>
        </div>
        """)

        # Add connector line between steps
        if i < len(steps) - 1:
            line_class = "step-line"
            if status == "completed" or (is_active and i > 0):
                line_class += " active"
            stepper_html.append(f'<div class="{line_class}"></div>')

    stepper_html.append('</div>')
    st.markdown("".join(stepper_html), unsafe_allow_html=True)


def render_status_pill(text: str, status_type: str = "info"):
    """Render a modern status pill."""
    type_classes = {
        "success": "pill-success",
        "warning": "pill-warning",
        "error": "pill-error",
        "info": "pill-info",
        "neutral": "pill-neutral",
    }
    css_class = type_classes.get(status_type, "pill-info")
    st.markdown(f'<span class="status-pill {css_class}">{text}</span>', unsafe_allow_html=True)


def render_feature_card(icon: str, title: str, description: str, tag: str = None):
    """Render a modern interactive feature card."""
    tag_html = f'<span class="card-tag">{tag}</span>' if tag else ''
    st.markdown(f"""
    <div class="modern-card">
        <div style="display: flex; justify-content: space-between; align-items: start;">
            <div class="card-icon">{icon}</div>
            {tag_html}
        </div>
        <h4 style="margin: 0.75rem 0 0.4rem; color: #1B2A4A; font-weight: 700;">{title}</h4>
        <p style="color: #64748B; font-size: 0.9rem; line-height: 1.5; margin: 0;">{description}</p>
    </div>
    """, unsafe_allow_html=True)
