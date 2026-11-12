"""Conversation History & Audit Log view for reviewing, archiving, or deleting chat sessions."""

from typing import Any

import streamlit as st

from frontend.components.ui_cards import (
    format_timestamp,
    render_active_resident_banner,
    render_safety_alert_banner,
)
from frontend.services.api_client import APIError
from frontend.services.chat_service import ChatFrontendService


SESSION_STATUS_FILTERS = ["all", "active", "archived", "closed"]


def render_conversations_view(chat_service: ChatFrontendService) -> None:
    """Render conversation session management and full transcript inspection."""
    token: str = st.session_state["token"]
    resident: dict[str, Any] | None = st.session_state.get("selected_resident")

    st.title("💬 Conversation History & Clinical Audit Log")
    render_active_resident_banner(resident)

    if not resident:
        return

    resident_id = resident["id"]

    fcol1, fcol2 = st.columns([3, 1])
    fcol1.subheader(f"📂 Conversations for {resident.get('name')}")
    status_filter = fcol2.selectbox(
        "Filter by Status",
        options=SESSION_STATUS_FILTERS,
        format_func=lambda s: "All Statuses" if s == "all" else s.upper(),
    )

    try:
        sessions = chat_service.list_sessions(
            token=token,
            resident_id=resident_id,
            status_filter=None if status_filter == "all" else status_filter,
        )
    except APIError as exc:
        st.error(f"Failed to load conversations: {exc.message}")
        return

    if not sessions:
        st.info("No conversation sessions match the current filter.")
        return

    for sess in sessions:
        sid = sess["id"]
        title = sess.get("title") or f"Conversation #{sid}"
        status_val = sess.get("status", "active")
        extra = sess.get("extra_metadata") or {}
        prov = extra.get("provider", "default")
        mod = extra.get("model", "default")

        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([3.5, 1.3, 1.3, 1.1])
            with c1:
                st.markdown(f"### #{sid} — {title}")
                st.caption(
                    f"Status: **`{status_val.upper()}`** • LLM: `{prov} / {mod}` • "
                    f"Created: `{format_timestamp(sess.get('created_at'))}` • "
                    f"Updated: `{format_timestamp(sess.get('updated_at'))}`"
                )
            with c2:
                if status_val == "active":
                    if st.button("💬 Resume in Chat", key=f"resume_conv_{sid}", use_container_width=True, type="primary"):
                        st.session_state["active_conversation_id"] = sid
                        st.session_state["active_page"] = "🤖 AI Companion Chat"
                        st.rerun()
                else:
                    if st.button("🔓 Reopen Session", key=f"reopen_conv_{sid}", use_container_width=True):
                        try:
                            chat_service.update_session(token, sid, status="active")
                            st.success(f"Reopened session #{sid}.")
                            st.rerun()
                        except APIError as exc:
                            st.error(exc.message)
            with c3:
                if status_val == "active":
                    if st.button("📦 Archive", key=f"archive_conv_{sid}", use_container_width=True):
                        try:
                            chat_service.update_session(token, sid, status="archived")
                            st.success(f"Archived session #{sid}.")
                            st.rerun()
                        except APIError as exc:
                            st.error(exc.message)
            with c4:
                if st.button("🗑️ Delete", key=f"del_conv_{sid}", use_container_width=True):
                    try:
                        chat_service.delete_session(token, sid)
                        if st.session_state.get("active_conversation_id") == sid:
                            st.session_state["active_conversation_id"] = None
                        st.success(f"Deleted session #{sid}.")
                        st.rerun()
                    except APIError as exc:
                        st.error(exc.message)

            with st.expander("📜 Inspect Full Transcript & Metadata"):
                try:
                    detail = chat_service.get_session_history(token, sid)
                    if isinstance(detail, list):
                        msgs = detail
                    elif isinstance(detail, dict):
                        msgs = detail.get("messages") or []
                    else:
                        msgs = []
                    if not msgs:
                        st.caption("No messages recorded in this session.")
                    else:
                        for m in msgs:
                            m_role = m.get("role", "user").upper()
                            m_meta = m.get("extra_metadata") or {}
                            st.markdown(
                                f"**[{m_role}]** (`{format_timestamp(m.get('created_at'))}`): {m.get('content')}"
                            )
                            if m_meta.get("safety"):
                                render_safety_alert_banner(m_meta.get("safety"))
                            if m_role == "ASSISTANT" and m_meta:
                                st.caption(
                                    f"Provider: `{m_meta.get('provider')}` • Model: `{m_meta.get('model')}` • "
                                    f"Latency: `{m_meta.get('latency_ms')} ms` • "
                                    f"Tokens: `{m_meta.get('token_usage', {}).get('total_tokens', 0)}`"
                                )
                            st.divider()
                except APIError as exc:
                    st.error(f"Failed to load transcript: {exc.message}")

