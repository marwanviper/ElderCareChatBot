"""Sidebar navigation and resident context selector for the Streamlit frontend."""

from typing import Any

import streamlit as st

from frontend.services.api_client import APIError
from frontend.services.care_service import CareService


NAVIGATION_PAGES = [
    "📊 Dashboard",
    "🤖 AI Companion Chat",
    "💬 Conversation History",
    "👥 Residents",
    "📋 Care Reports",
    "🎯 Care Goals",
    "⚠️ Adverse Incidents",
]


def render_sidebar(care_service: CareService) -> str:
    """Render sidebar with user profile, active resident selector, and navigation menu."""
    user: dict[str, Any] = st.session_state.get("user") or {}
    token: str | None = st.session_state.get("token")

    with st.sidebar:
        st.markdown("## 🏥 ElderCare AI")
        st.caption("Clinical Care & Conversational AI Platform")
        st.divider()

        # User profile summary
        role_badge = "🛡️ Admin" if user.get("role") == "admin" else "🩺 Caregiver"
        st.markdown(f"**Signed in as:** {user.get('name', 'User')}")
        st.caption(f"{role_badge} • `{user.get('email', '')}`")

        # Load accessible residents into session state
        if token and ("residents_cache" not in st.session_state or st.session_state.get("refresh_residents")):
            try:
                st.session_state["residents_cache"] = care_service.list_residents(token)
                st.session_state["refresh_residents"] = False
            except APIError as exc:
                st.error(f"Could not load residents: {exc.message}")
                st.session_state["residents_cache"] = []

        residents: list[dict[str, Any]] = st.session_state.get("residents_cache", [])

        st.divider()
        st.markdown("### 👤 Active Resident Context")
        if residents:
            resident_options = {
                r["id"]: f"{r['name']} (Room {r.get('room_number') or 'N/A'})"
                for r in residents
            }
            resident_ids = list(resident_options.keys())

            current_res_id = st.session_state.get("selected_resident_id")
            if current_res_id not in resident_ids:
                current_res_id = resident_ids[0]
                st.session_state["selected_resident_id"] = current_res_id

            selected_id = st.selectbox(
                "Select Resident",
                options=resident_ids,
                index=resident_ids.index(current_res_id),
                format_func=lambda rid: resident_options.get(rid, f"Resident #{rid}"),
                key="sidebar_resident_select",
            )
            st.session_state["selected_resident_id"] = selected_id
            st.session_state["selected_resident"] = next(
                (r for r in residents if r["id"] == selected_id),
                None,
            )
        else:
            st.session_state["selected_resident_id"] = None
            st.session_state["selected_resident"] = None
            st.caption("No residents accessible yet.")

        if st.button("🔄 Refresh Resident List", use_container_width=True):
            st.session_state["refresh_residents"] = True
            st.rerun()

        st.divider()
        st.markdown("### 🧭 Navigation")

        default_page = st.session_state.get("active_page", NAVIGATION_PAGES[0])
        if default_page not in NAVIGATION_PAGES:
            default_page = NAVIGATION_PAGES[0]

        selected_page = st.radio(
            "Go to module",
            options=NAVIGATION_PAGES,
            index=NAVIGATION_PAGES.index(default_page),
            label_visibility="collapsed",
        )
        st.session_state["active_page"] = selected_page

        st.divider()
        if st.button("🚪 Sign Out", use_container_width=True, type="secondary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    return selected_page

