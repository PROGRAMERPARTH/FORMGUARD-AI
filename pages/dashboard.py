"""
FORMGUARD AI - Dashboard Page
Displays verification session statistics and recent activity.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime


def render_dashboard():
    """Render the user dashboard."""
    # Header
    st.markdown("""
    <div class="formguard-header">
        <h1>📊 Dashboard</h1>
        <div class="tagline">Overview of your verification activity</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Metrics Row ──
    col1, col2, col3, col4 = st.columns(4)

    # Calculate real metrics from session state
    sessions = st.session_state.get("sessions_history", [])
    total_sessions = len(sessions)
    total_docs = st.session_state.get("total_docs_processed", 0)
    total_issues = st.session_state.get("total_issues_found", 0)
    total_reports = st.session_state.get("total_reports_generated", 0)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_sessions}</div>
            <div class="metric-label">Verification Sessions</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_docs}</div>
            <div class="metric-label">Documents Processed</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_issues}</div>
            <div class="metric-label">Issues Identified</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_reports}</div>
            <div class="metric-label">Reports Generated</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Verification Results Chart ──
    if st.session_state.get("verification_result"):
        result = st.session_state.verification_result

        col_chart, col_summary = st.columns([2, 1])

        with col_chart:
            st.markdown("#### Verification Results Distribution")
            fig = go.Figure(data=[go.Pie(
                labels=["Pass", "Warning", "Critical", "Manual Review"],
                values=[
                    result.get("pass_count", 0),
                    result.get("warning_count", 0),
                    result.get("critical_count", 0),
                    result.get("manual_review_count", 0),
                ],
                hole=0.5,
                marker_colors=["#10B981", "#F59E0B", "#EF4444", "#3B82F6"],
                textinfo="label+value",
                textfont_size=13,
            )])
            fig.update_layout(
                showlegend=True,
                height=350,
                margin=dict(t=20, b=20, l=20, r=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter"),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_summary:
            st.markdown("#### Readiness Score")
            readiness = result.get("overall_readiness", 0)

            # Readiness gauge
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=readiness,
                title={"text": "Application Readiness", "font": {"size": 16}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1},
                    "bar": {"color": "#10B981" if readiness >= 80 else "#F59E0B" if readiness >= 50 else "#EF4444"},
                    "bgcolor": "white",
                    "steps": [
                        {"range": [0, 50], "color": "#FEE2E2"},
                        {"range": [50, 80], "color": "#FEF3C7"},
                        {"range": [80, 100], "color": "#D1FAE5"},
                    ],
                },
                number={"suffix": "%", "font": {"size": 36}},
            ))
            fig_gauge.update_layout(
                height=250,
                margin=dict(t=50, b=20, l=30, r=30),
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter"),
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

            # Quick stats
            total_checks = (result.get("pass_count", 0) + result.get("warning_count", 0) +
                          result.get("critical_count", 0) + result.get("manual_review_count", 0))
            st.markdown(f"**Total Checks:** {total_checks}")
            st.markdown(f"**Scheme:** {result.get('scheme_name', 'N/A')}")
            st.markdown(f"**Academic Year:** {result.get('academic_year', 'N/A')}")

    else:
        # Empty state
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="info-card" style="text-align: center; padding: 3rem;">
            <p style="font-size: 3rem; margin-bottom: 1rem;">📋</p>
            <h3>No Verification Sessions Yet</h3>
            <p style="color: var(--text-secondary);">
                Start your first verification to see your dashboard come to life.<br>
                Upload your documents and let FORMGUARD AI check them for you.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Recent Sessions ──
    if sessions:
        st.markdown("#### Recent Verification Sessions")
        for session in reversed(sessions[-5:]):
            status_color = "#10B981" if session.get("status") == "completed" else "#F59E0B"
            st.markdown(f"""
            <div class="info-card" style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>{session.get('scheme_name', 'Unknown Scheme')}</strong>
                    <br><span style="color: var(--text-secondary); font-size: 0.85rem;">
                        {session.get('academic_year', '')} | {session.get('docs_count', 0)} documents
                    </span>
                </div>
                <div>
                    <span class="badge" style="background: {status_color}22; color: {status_color};">
                        {session.get('status', 'unknown').upper()}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Start New Verification ──
    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        if st.button("🚀 Start New Verification", type="primary", use_container_width=True):
            # Reset session for new verification
            st.session_state.session_id = None
            st.session_state.scheme_id = None
            st.session_state.uploaded_documents = {}
            st.session_state.extractions = {}
            st.session_state.verification_result = None
            st.session_state.verification_report = None
            st.session_state.current_page = "upload"
            st.rerun()
