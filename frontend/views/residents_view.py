"""Resident management and caregiver permission assignment view."""

from datetime import date
from typing import Any

import streamlit as st

from frontend.components.ui_cards import render_active_resident_banner
from frontend.services.api_client import APIError
from frontend.services.auth_service import AuthService
from frontend.services.care_service import CareService


def render_residents_view(
    care_service: CareService,
    auth_service: AuthService,
) -> None:
    """Render Resident CRUD and Admin Caregiver-Resident Permission management."""
    token: str = st.session_state["token"]
    user: dict[str, Any] = st.session_state.get("user") or {}
    is_admin = user.get("role") == "admin"
    active_resident: dict[str, Any] | None = st.session_state.get("selected_resident")

    st.title("👥 Resident Directory & Access Management")
    render_active_resident_banner(active_resident)

    tabs = ["📋 Resident Directory", "✏️ Edit Selected Resident"]
    if is_admin:
        tabs.extend(["➕ Admit New Resident (Admin)", "🔐 Caregiver Permissions (Admin)"])

    rendered_tabs = st.tabs(tabs)

    # -------------------------------------------------------------------------
    # Tab 1: Resident Directory
    # -------------------------------------------------------------------------
    with rendered_tabs[0]:
        residents: list[dict[str, Any]] = st.session_state.get("residents_cache", [])
        search_query = st.text_input(
            "🔍 Filter residents by name or room number",
            placeholder="Type resident name or room...",
        ).strip().lower()

        filtered = [
            r
            for r in residents
            if not search_query
            or search_query in r.get("name", "").lower()
            or search_query in str(r.get("room_number") or "").lower()
        ]

        if not filtered:
            st.info("No matching residents found.")
        else:
            for res in filtered:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 2, 2])
                    with c1:
                        st.markdown(f"### {res.get('name')} (ID #{res.get('id')})")
                        st.caption(
                            f"🚪 Room: **{res.get('room_number') or 'Unassigned'}**  |  "
                            f"🎂 DOB: **{res.get('date_of_birth') or 'Not set'}**"
                        )
                    with c2:
                        if st.button(
                            "Set as Active Resident",
                            key=f"select_res_btn_{res['id']}",
                            use_container_width=True,
                        ):
                            st.session_state["selected_resident_id"] = res["id"]
                            st.session_state["selected_resident"] = res
                            st.rerun()
                    with c3:
                        if is_admin:
                            if st.button(
                                "🗑️ Delete Resident",
                                key=f"del_res_btn_{res['id']}",
                                type="secondary",
                                use_container_width=True,
                            ):
                                try:
                                    care_service.delete_resident(token, res["id"])
                                    st.session_state["refresh_residents"] = True
                                    st.success(f"Deleted resident #{res['id']}.")
                                    st.rerun()
                                except APIError as exc:
                                    st.error(f"Delete failed: {exc.message}")

    # -------------------------------------------------------------------------
    # Tab 2: Edit Selected Resident
    # -------------------------------------------------------------------------
    with rendered_tabs[1]:
        if not active_resident:
            st.info("Select a resident first to edit their profile.")
        else:
            with st.form("edit_resident_form"):
                st.subheader(f"Update Profile — {active_resident.get('name')}")
                new_name = st.text_input("Full Name", value=active_resident.get("name", ""))
                new_room = st.text_input(
                    "Room Number",
                    value=active_resident.get("room_number") or "",
                )
                current_dob_str = active_resident.get("date_of_birth")
                default_dob = date(1945, 1, 1)
                if current_dob_str:
                    try:
                        default_dob = date.fromisoformat(str(current_dob_str))
                    except ValueError:
                        pass
                include_dob = st.checkbox("Update Date of Birth", value=bool(current_dob_str))
                new_dob = st.date_input(
                    "Date of Birth",
                    value=default_dob,
                    min_value=date(1900, 1, 1),
                    max_value=date.today(),
                )
                save_edit = st.form_submit_button("Save Changes", type="primary")
                if save_edit:
                    try:
                        updated = care_service.update_resident(
                            token=token,
                            resident_id=active_resident["id"],
                            name=new_name,
                            room_number=new_room,
                            date_of_birth=new_dob if include_dob else None,
                        )
                        st.session_state["selected_resident"] = updated
                        st.session_state["refresh_residents"] = True
                        st.success("Resident profile updated successfully.")
                        st.rerun()
                    except APIError as exc:
                        st.error(f"Update failed: {exc.message}")

    # -------------------------------------------------------------------------
    # Tab 3 (Admin): Admit New Resident
    # -------------------------------------------------------------------------
    if is_admin:
        with rendered_tabs[2]:
            with st.form("admit_resident_form", clear_on_submit=True):
                st.subheader("Admit New Resident")
                admit_name = st.text_input("Resident Full Name", placeholder="Arthur Pendelton")
                admit_room = st.text_input("Assigned Room Number", placeholder="204B")
                specify_dob = st.checkbox("Specify Date of Birth", value=True)
                admit_dob = st.date_input(
                    "Date of Birth",
                    value=date(1940, 6, 15),
                    min_value=date(1900, 1, 1),
                    max_value=date.today(),
                )
                submit_admit = st.form_submit_button("Admit Resident", type="primary")
                if submit_admit:
                    if not admit_name.strip():
                        st.warning("Resident name is required.")
                    else:
                        try:
                            created = care_service.create_resident(
                                token=token,
                                name=admit_name,
                                date_of_birth=admit_dob if specify_dob else None,
                                room_number=admit_room or None,
                            )
                            st.session_state["selected_resident_id"] = created["id"]
                            st.session_state["refresh_residents"] = True
                            st.success(f"Admitted resident **{created['name']}** (ID #{created['id']}).")
                            st.rerun()
                        except APIError as exc:
                            st.error(f"Failed to admit resident: {exc.message}")

        # ---------------------------------------------------------------------
        # Tab 4 (Admin): Caregiver-Resident Permissions
        # ---------------------------------------------------------------------
        with rendered_tabs[3]:
            if not active_resident:
                st.info("Select an active resident to manage caregiver permissions.")
            else:
                st.subheader(
                    f"Caregiver Access Permissions for {active_resident.get('name')} (ID #{active_resident['id']})"
                )
                try:
                    all_users = auth_service.list_users(token)
                    current_perms = care_service.list_resident_permissions(
                        token, active_resident["id"]
                    )
                    assigned_user_ids = {p["user_id"] for p in current_perms}
                    user_map = {u["id"]: u for u in all_users}

                    st.markdown("#### Currently Assigned Caregivers / Users")
                    if not current_perms:
                        st.caption("No caregivers explicitly assigned yet (Admins always have access).")
                    else:
                        for perm in current_perms:
                            uid = perm["user_id"]
                            uinfo = user_map.get(uid, {})
                            pcol1, pcol2 = st.columns([4, 1])
                            pcol1.write(
                                f"• **{uinfo.get('name', f'User #{uid}')}** "
                                f"(`{uinfo.get('email', 'N/A')}`, role: `{uinfo.get('role', 'N/A')}`)"
                            )
                            if pcol2.button("Revoke", key=f"revoke_{uid}_{active_resident['id']}"):
                                care_service.revoke_permission(token, uid, active_resident["id"])
                                st.success(f"Revoked permission for user #{uid}.")
                                st.rerun()

                    st.divider()
                    st.markdown("#### Grant Access to Caregiver")
                    unassigned_users = [
                        u for u in all_users if u["id"] not in assigned_user_ids
                    ]
                    if not unassigned_users:
                        st.caption("All registered users already have access to this resident.")
                    else:
                        with st.form("grant_perm_form"):
                            selected_uid = st.selectbox(
                                "Select User",
                                options=[u["id"] for u in unassigned_users],
                                format_func=lambda uid: f"{user_map[uid]['name']} ({user_map[uid]['email']} - {user_map[uid]['role']})",
                            )
                            if st.form_submit_button("Grant Access Permission", type="primary"):
                                care_service.assign_permission(
                                    token,
                                    user_id=selected_uid,
                                    resident_id=active_resident["id"],
                                )
                                st.success("Access permission granted!")
                                st.rerun()
                except APIError as exc:
                    st.error(f"Could not load permissions: {exc.message}")

