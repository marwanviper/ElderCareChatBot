"""Dashboard overview page for the ElderCareChatBot Streamlit frontend."""

from typing import Any

import streamlit as st

from frontend.components.ui_cards import format_timestamp, render_active_resident_banner
from frontend.services.api_client import APIError
from frontend.services.care_service import CareService
from frontend.services.chat_service import ChatFrontendService


def render_dashboard_view(
    care_service: CareService,
    chat_service: ChatFrontendService,
) -> None:
    """Render facility & active-resident summary metrics and quick actions."""
    token: str = st.session_state["token"]
    resident: dict[str, Any] | None = st.session_state.get("selected_resident")
    residents: list[dict[str, Any]] = st.session_state.get("residents_cache", [])

    st.title("📊 Clinical Care & AI Overview Dashboard")
    render_active_resident_banner(resident)

    if not resident:
        st.warning(
            "No resident is currently available in your view. "
            "Administrators can admit residents in the **👥 Residents** page and assign caregiver permissions."
        )
        return

    resident_id = resident["id"]

    # Fetch resident-scoped telemetry
    reports: list[dict[str, Any]] = []
    goals: list[dict[str, Any]] = []
    incidents: list[dict[str, Any]] = []
    sessions: list[dict[str, Any]] = []

    try:
        reports = care_service.list_resident_care_reports(token, resident_id, limit=20)
        goals = care_service.list_resident_care_goals(token, resident_id, limit=20)
        incidents = care_service.list_resident_incidents(token, resident_id, limit=20)
        sessions = chat_service.list_sessions(token, resident_id=resident_id, limit=20)
    except APIError as exc:
        st.error(f"Failed to load resident dashboard data: {exc.message}")

    active_goals = [g for g in goals if g.get("status") == "active"]
    active_sessions = [s for s in sessions if s.get("status") == "active"]

    # Top KPI row
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Accessible Residents", len(residents))
    col2.metric("Care Reports", len(reports))
    col3.metric("Active Care Goals", len(active_goals))
    col4.metric("Logged Incidents", len(incidents))
    col5.metric("AI Chat Sessions", len(active_sessions))

    st.divider()

    # Quick navigation buttons
    qcol1, qcol2, qcol3, qcol4 = st.columns(4)
    if qcol1.button("🤖 Launch AI Companion Chat", use_container_width=True, type="primary"):
        st.session_state["active_page"] = "🤖 AI Companion Chat"
        st.rerun()
    if qcol2.button("📋 Write Care Report", use_container_width=True):
        st.session_state["active_page"] = "📋 Care Reports"
        st.rerun()
    if qcol3.button("🎯 Manage Care Goals", use_container_width=True):
        st.session_state["active_page"] = "🎯 Care Goals"
        st.rerun()
    if qcol4.button("⚠️ Log Adverse Incident", use_container_width=True):
        st.session_state["active_page"] = "⚠️ Adverse Incidents"
        st.rerun()

    st.divider()

    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("📋 Recent Care Reports")
        if not reports:
            st.caption("No care reports recorded for this resident yet.")
        else:
            for rep in reports[:4]:
                with st.container(border=True):
                    st.caption(f"🕒 {format_timestamp(rep.get('report_date'))} • Report #{rep.get('id')}")
                    st.write(rep.get("content", ""))

        st.subheader("🎯 Active Care Goals")
        if not active_goals:
            st.caption("No active care goals for this resident.")
        else:
            for goal in active_goals[:4]:
                with st.container(border=True):
                    st.markdown(f"**Goal #{goal.get('id')}:** {goal.get('goal')}")
                    st.caption(f"Status: `{goal.get('status')}` • Created: {format_timestamp(goal.get('created_at'))}")

    with right_col:
        st.subheader("⚠️ Recent Adverse Incidents")
        if not incidents:
            st.caption("No adverse incidents recorded for this resident.")
        else:
            for inc in incidents[:4]:
                with st.container(border=True):
                    st.markdown(
                        f"**[{inc.get('type')}]** — {format_timestamp(inc.get('incident_date'))}"
                    )
                    st.write(inc.get("description", ""))

        st.subheader("💬 Recent AI Companion Sessions")
        if not sessions:
            st.caption("No AI conversations started for this resident yet.")
        else:
            for sess in sessions[:4]:
                meta = sess.get("extra_metadata") or {}
                provider_label = meta.get("provider", "default")
                model_label = meta.get("model", "default")
                sess_title = sess.get("title") or f"Conversation #{sess.get('id')}"
                with st.container(border=True):
                    st.markdown(f"**{sess_title}**")
                    st.caption(
                        f"Status: `{sess.get('status')}` • LLM: `{provider_label} / {model_label}` • "
                        f"Updated: {format_timestamp(sess.get('updated_at'))}"
                    )
                    if st.button(
                        "Open in Chat",
                        key=f"dash_open_sess_{sess['id']}",
                    ):
                        st.session_state["active_conversation_id"] = sess["id"]
                        st.session_state["active_page"] = "🤖 AI Companion Chat"
                        st.rerun()

