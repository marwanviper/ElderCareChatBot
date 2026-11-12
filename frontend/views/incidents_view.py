"""Adverse Incidents view for logging and managing resident safety events."""

from typing import Any

import streamlit as st

from frontend.components.ui_cards import format_timestamp, render_active_resident_banner
from frontend.services.api_client import APIError
from frontend.services.care_service import CareService


INCIDENT_CATEGORIES = [
    "Fall",
    "Medication",
    "Behavioral",
    "Clinical / Vital Sign",
    "Mobility / Skin Integrity",
    "Other",
]


def render_incidents_view(care_service: CareService) -> None:
    """Render adverse incident reporting and history for the active resident."""
    token: str = st.session_state["token"]
    user: dict[str, Any] = st.session_state.get("user") or {}
    is_admin = user.get("role") == "admin"
    resident: dict[str, Any] | None = st.session_state.get("selected_resident")

    st.title("⚠️ Adverse Incidents & Safety Log")
    render_active_resident_banner(resident)

    if not resident:
        return

    resident_id = resident["id"]

    with st.expander("🚨 Log New Adverse Incident", expanded=True):
        with st.form("create_incident_form", clear_on_submit=True):
            inc_type = st.selectbox("Incident Category", options=INCIDENT_CATEGORIES)
            inc_desc = st.text_area(
                "Incident Details & Immediate Actions Taken",
                placeholder="Describe what happened, vital signs checked, physician notification, and follow-up measures...",
                height=110,
            )
            if st.form_submit_button("Record Adverse Incident", type="primary"):
                if not inc_desc.strip():
                    st.warning("Please provide a description of the incident.")
                else:
                    try:
                        care_service.create_incident(
                            token=token,
                            resident_id=resident_id,
                            incident_type=inc_type,
                            description=inc_desc,
                        )
                        st.success("Adverse incident logged.")
                        st.rerun()
                    except APIError as exc:
                        st.error(f"Failed to log incident: {exc.message}")

    st.divider()
    st.subheader(f"📂 Recorded Incidents — {resident.get('name')}")

    try:
        incidents = care_service.list_resident_incidents(token, resident_id)
    except APIError as exc:
        st.error(f"Failed to load incidents: {exc.message}")
        return

    if not incidents:
        st.info("No adverse incidents recorded for this resident.")
        return

    for inc in incidents:
        inc_id = inc["id"]
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.markdown(
                f"**Incident #{inc_id} — [{inc.get('type')}]** • "
                f"🕒 `{format_timestamp(inc.get('incident_date'))}`"
            )
            if is_admin and c2.button("🗑️ Delete", key=f"del_inc_{inc_id}"):
                try:
                    care_service.delete_incident(token, inc_id)
                    st.success(f"Deleted incident #{inc_id}.")
                    st.rerun()
                except APIError as exc:
                    st.error(f"Delete failed: {exc.message}")

            st.write(inc.get("description", ""))

            with st.expander("✏️ Update Incident Notes"):
                with st.form(f"upd_inc_form_{inc_id}"):
                    upd_type = st.text_input("Category", value=inc.get("type", "Fall"))
                    upd_desc = st.text_area(
                        "Description",
                        value=inc.get("description", ""),
                        key=f"upd_inc_desc_{inc_id}",
                    )
                    if st.form_submit_button("Save Incident Update"):
                        try:
                            care_service.update_incident(
                                token=token,
                                incident_id=inc_id,
                                incident_type=upd_type,
                                description=upd_desc,
                            )
                            st.success(f"Incident #{inc_id} updated.")
                            st.rerun()
                        except APIError as exc:
                            st.error(f"Update failed: {exc.message}")

