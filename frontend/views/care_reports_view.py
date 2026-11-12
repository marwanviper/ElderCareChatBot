"""Care Reports view for creating, viewing, updating, and deleting clinical/daily care reports."""

from typing import Any

import streamlit as st

from frontend.components.ui_cards import format_timestamp, render_active_resident_banner
from frontend.services.api_client import APIError
from frontend.services.care_service import CareService


def render_care_reports_view(care_service: CareService) -> None:
    """Render clinical and daily care report management for the active resident."""
    token: str = st.session_state["token"]
    resident: dict[str, Any] | None = st.session_state.get("selected_resident")

    st.title("📋 Daily & Clinical Care Reports")
    render_active_resident_banner(resident)

    if not resident:
        return

    resident_id = resident["id"]

    with st.expander("➕ Author New Care Report", expanded=True):
        with st.form("create_care_report_form", clear_on_submit=True):
            content = st.text_area(
                "Clinical / Daily Observation Notes",
                placeholder="Document resident mood, meals, mobility, vital observations, or social activities...",
                height=110,
            )
            submitted = st.form_submit_button("Submit Care Report", type="primary")
            if submitted:
                if not content.strip():
                    st.warning("Report content cannot be empty.")
                else:
                    try:
                        care_service.create_care_report(
                            token=token,
                            resident_id=resident_id,
                            content=content,
                        )
                        st.success("Care report saved successfully.")
                        st.rerun()
                    except APIError as exc:
                        st.error(f"Could not save care report: {exc.message}")

    st.divider()
    st.subheader(f"📜 Care Report History — {resident.get('name')}")

    try:
        reports = care_service.list_resident_care_reports(token, resident_id)
    except APIError as exc:
        st.error(f"Failed to load care reports: {exc.message}")
        return

    if not reports:
        st.info("No care reports have been authored for this resident yet.")
        return

    for rep in reports:
        rep_id = rep["id"]
        with st.container(border=True):
            hcol1, hcol2 = st.columns([4, 1])
            hcol1.markdown(
                f"**Report #{rep_id}** • 🕒 `{format_timestamp(rep.get('report_date'))}` "
                f"• Author ID: `{rep.get('created_by') or 'System'}`"
            )
            if hcol2.button("🗑️ Delete", key=f"del_rep_{rep_id}"):
                try:
                    care_service.delete_care_report(token, rep_id)
                    st.success(f"Deleted report #{rep_id}.")
                    st.rerun()
                except APIError as exc:
                    st.error(f"Could not delete report: {exc.message}")

            st.write(rep.get("content", ""))

            with st.expander("✏️ Edit Report Content"):
                with st.form(f"edit_rep_form_{rep_id}"):
                    updated_text = st.text_area(
                        "Updated Content",
                        value=rep.get("content", ""),
                        key=f"edit_rep_txt_{rep_id}",
                    )
                    if st.form_submit_button("Save Update"):
                        try:
                            care_service.update_care_report(
                                token=token,
                                report_id=rep_id,
                                content=updated_text,
                            )
                            st.success(f"Report #{rep_id} updated.")
                            st.rerun()
                        except APIError as exc:
                            st.error(f"Update failed: {exc.message}")

