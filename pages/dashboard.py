"""
FORMGUARD AI - Dashboard Page
Displays verification session statistics, visual charts, and recent preflight history.
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime


def render_dashboard():
    """Render the user dashboard."""
    # Header
    st.markdown("""
    <div class="formguard-header">
        <h1>📊 Verification Intelligence Dashboard</h1>
        <div class="tagline">Real-time metrics, verification distributions, and preflight audit history</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Real Metrics Calculation ──
    sessions = st.session_state.get("sessions_history", [])
    total_sessions = len(sessions)
    total_docs = st.session_state.get("total_docs_processed", 0)
    total_issues = st.session_state.get("total_issues_found", 0)
    total_reports = st.session_state.get("total_reports_generated", 0)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card" style="border-top: 3px solid #1B2A4A;">
            <div class="metric-value">{total_sessions}</div>
            <div class="metric-label">Preflight Sessions</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card" style="border-top: 3px solid #2E5090;">
            <div class="metric-value">{total_docs}</div>
            <div class="metric-label">Documents Audited</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card" style="border-top: 3px solid #F59E0B;">
            <div class="metric-value">{total_issues}</div>
            <div class="metric-label">Prevented Errors</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card" style="border-top: 3px solid #10B981;">
            <div class="metric-value">{total_reports}</div>
            <div class="metric-label">Reports Generated</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Active Verification Visualization ──
    v_res = st.session_state.get("verification_result")

    if v_res:
        ch_col1, ch_col2 = st.columns([1.5, 1])

        with ch_col1:
            st.markdown("#### 🍩 Checks Outcome Distribution")
            pass_c = v_res.get("pass_count", 0)
            warn_c = v_res.get("warning_count", 0)
            crit_c = v_res.get("critical_count", 0)
            man_c = v_res.get("manual_review_count", 0)

            fig = go.Figure(data=[go.Pie(
                labels=["Passed", "Warnings", "Critical Discrepancies", "Manual Review"],
                values=[pass_c, warn_c, crit_c, man_c],
                hole=0.55,
                marker_colors=["#10B981", "#F59E0B", "#EF4444", "#3B82F6"],
                textinfo="label+value",
                textfont=dict(family="Inter", size=12),
                hoverinfo="label+value+percent",
            )])
            fig.update_layout(
                showlegend=True,
                height=320,
                margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#1E293B"),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig, use_container_width=True)

        with ch_col2:
            st.markdown("#### 🎯 Overall Application Readiness")
            readiness = v_res.get("overall_readiness", 0)
            gauge_color = "#10B981" if readiness >= 80 else "#F59E0B" if readiness >= 50 else "#EF4444"

            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=readiness,
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#94A3B8"},
                    "bar": {"color": gauge_color, "thickness": 0.3},
                    "bgcolor": "#F1F5F9",
                    "steps": [
                        {"range": [0, 50], "color": "#FEE2E2"},
                        {"range": [50, 80], "color": "#FEF3C7"},
                        {"range": [80, 100], "color": "#D1FAE5"},
                    ],
                },
                number={"suffix": "%", "font": {"size": 38, "family": "Inter", "color": gauge_color}},
            ))
            fig_gauge.update_layout(
                height=260,
                margin=dict(t=20, b=10, l=20, r=20),
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

            # Details card
            st.markdown(f"""
            <div style="background: white; border: 1px solid var(--border); border-radius: 8px; padding: 0.75rem 1rem; font-size: 0.85rem;">
                <strong>Target Scheme:</strong> {v_res.get('scheme_name', 'MahaDBT')}<br>
                <strong>Academic Year:</strong> {v_res.get('academic_year', '2026-2027')}<br>
                <strong>Reservation Category:</strong> {v_res.get('applicant_category', 'General')}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="info-card" style="text-align: center; padding: 2.5rem 1.5rem;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📋</div>
            <h4 style="margin: 0 0 0.5rem; color: #1B2A4A;">No Verification Session Active</h4>
            <p style="color: var(--text-secondary); font-size: 0.9rem; max-width: 500px; margin: 0 auto 1.5rem;">
                Run your first document verification session to see interactive analytics, error trends, and compliance readiness here.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Recent Sessions History ──
    if sessions:
        st.markdown("#### 🕒 Recent Preflight Sessions")
        for sess in reversed(sessions[-5:]):
            s_readiness = sess.get("readiness", 0)
            badge_cls = "badge-pass" if s_readiness >= 80 else "badge-warning" if s_readiness >= 50 else "badge-critical"

            st.markdown(f"""
            <div style="background: white; border: 1px solid var(--border); border-radius: 8px; padding: 0.85rem 1.25rem; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center; box-shadow: var(--shadow-sm);">
                <div>
                    <strong style="color: #1E293B;">{sess.get('scheme_name', 'Scholarship')}</strong>
                    <div style="color: #64748B; font-size: 0.82rem; margin-top: 0.2rem;">
                        Year: {sess.get('academic_year', '')} • {sess.get('docs_count', 0)} documents processed
                    </div>
                </div>
                <div>
                    <span class="badge {badge_cls}">
                        {s_readiness:.0f}% Readiness
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Interactive Quick Actions ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    act_col1, act_col2, act_col3 = st.columns([1, 1.5, 1])

    with act_col2:
        if st.button("🚀 Start New Application Preflight", type="primary", use_container_width=True):
            st.session_state.session_id = None
            st.session_state.uploaded_documents = {}
            st.session_state.extractions = {}
            st.session_state.verification_result = None
            st.session_state.current_page = "upload"
            st.rerun()
