"""Care Goals view for establishing and tracking resident care goals."""

from typing import Any

import streamlit as st

from frontend.components.ui_cards import format_timestamp, render_active_resident_banner
from frontend.services.api_client import APIError
from frontend.services.care_service import CareService


GOAL_STATUS_OPTIONS = ["active", "achieved", "on_hold", "cancelled"]


def render_care_goals_view(care_service: CareService) -> None:
    """Render care goal creation, status filtering, and lifecycle updates."""
    token: str = st.session_state["token"]
    user: dict[str, Any] = st.session_state.get("user") or {}
    is_admin = user.get("role") == "admin"
    resident: dict[str, Any] | None = st.session_state.get("selected_resident")

    st.title("🎯 Resident Care Goals")
    render_active_resident_banner(resident)

    if not resident:
        return

    resident_id = resident["id"]

    with st.expander("➕ Establish New Care Goal", expanded=True):
        with st.form("create_care_goal_form", clear_on_submit=True):
            goal_text = st.text_area(
                "Care Goal Description",
                placeholder="e.g., Walk 200 meters daily in the courtyard with walker assistance.",
                height=90,
            )
            initial_status = st.selectbox("Initial Status", options=GOAL_STATUS_OPTIONS, index=0)
            if st.form_submit_button("Create Care Goal", type="primary"):
                if not goal_text.strip():
                    st.warning("Please enter a care goal description.")
                else:
                    try:
                        care_service.create_care_goal(
                            token=token,
                            resident_id=resident_id,
                            goal=goal_text,
                            status=initial_status,
                        )
                        st.success("Care goal created.")
                        st.rerun()
                    except APIError as exc:
                        st.error(f"Failed to create goal: {exc.message}")

    st.divider()
    fcol1, fcol2 = st.columns([3, 1])
    fcol1.subheader(f"🎯 Care Goals — {resident.get('name')}")
    status_filter = fcol2.selectbox(
        "Filter by Status",
        options=["all"] + GOAL_STATUS_OPTIONS,
        format_func=lambda s: "All Statuses" if s == "all" else s.upper(),
    )

    try:
        goals = care_service.list_resident_care_goals(
            token=token,
            resident_id=resident_id,
            status_filter=None if status_filter == "all" else status_filter,
        )
    except APIError as exc:
        st.error(f"Failed to load care goals: {exc.message}")
        return

    if not goals:
        st.info("No care goals match the current filter.")
        return

    for g in goals:
        gid = g["id"]
        current_status = g.get("status", "active")
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.markdown(
                f"**Goal #{gid}** • Status: `{current_status.upper()}` • "
                f"Created: `{format_timestamp(g.get('created_at'))}`"
            )
            if is_admin and c2.button("🗑️ Delete", key=f"del_goal_{gid}"):
                try:
                    care_service.delete_care_goal(token, gid)
                    st.success(f"Deleted goal #{gid}.")
                    st.rerun()
                except APIError as exc:
                    st.error(f"Delete failed: {exc.message}")

            st.write(g.get("goal", ""))

            with st.expander("✏️ Update Goal or Transition Status"):
                with st.form(f"upd_goal_form_{gid}"):
                    new_goal_txt = st.text_input("Goal Description", value=g.get("goal", ""))
                    status_idx = (
                        GOAL_STATUS_OPTIONS.index(current_status)
                        if current_status in GOAL_STATUS_OPTIONS
                        else 0
                    )
                    new_status = st.selectbox(
                        "Status",
                        options=GOAL_STATUS_OPTIONS,
                        index=status_idx,
                        key=f"goal_status_sel_{gid}",
                    )
                    if st.form_submit_button("Save Goal Changes"):
                        try:
                            care_service.update_care_goal(
                                token=token,
                                goal_id=gid,
                                goal=new_goal_txt,
                                status=new_status,
                            )
                            st.success(f"Goal #{gid} updated.")
                            st.rerun()
                        except APIError as exc:
                            st.error(f"Update failed: {exc.message}")

