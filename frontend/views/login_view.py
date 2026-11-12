"""Authentication view (Sign In and Account Registration) for the Streamlit frontend."""

import streamlit as st

from frontend.config import frontend_config
from frontend.services.api_client import APIError
from frontend.services.auth_service import AuthService


def render_login_view(auth_service: AuthService) -> None:
    """Render the login and registration page when no user is authenticated."""
    st.markdown("## 🏥 ElderCare AI — Care Management & Companion Platform")
    st.caption(
        "Secure clinical portal for caregivers and administrators, integrated with LangGraph AI Companion (Google Gemini & OpenAI GPT-3.5)."
    )

    # Check backend health status
    col_status, _ = st.columns([1, 2])
    with col_status:
        try:
            health = auth_service.client.check_health()
            if health.get("status") == "healthy":
                st.success(f"Backend Connected ({frontend_config.API_BASE_URL})")
            else:
                st.warning(f"Backend status: {health}")
        except APIError as exc:
            st.error(exc.message)

    tab_login, tab_register = st.tabs(["🔐 Sign In", "📝 Register New Account"])

    with tab_login:
        with st.form("login_form", clear_on_submit=False):
            st.subheader("Sign In to Your Account")
            email = st.text_input("Email Address", placeholder="caregiver@eldercare.org")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)

            if submitted:
                if not email.strip() or not password:
                    st.warning("Please enter both your email address and password.")
                else:
                    try:
                        token_resp = auth_service.login(email=email, password=password)
                        access_token = token_resp["access_token"]
                        user_profile = auth_service.get_current_user(access_token)

                        st.session_state["token"] = access_token
                        st.session_state["user"] = user_profile
                        st.session_state["refresh_residents"] = True
                        st.success(f"Welcome back, {user_profile.get('name')}!")
                        st.rerun()
                    except APIError as exc:
                        st.error(f"Sign in failed: {exc.message}")

    with tab_register:
        with st.form("register_form", clear_on_submit=True):
            st.subheader("Create a Caregiver or Administrator Account")
            reg_name = st.text_input("Full Name", placeholder="Dr. Elena Rostova")
            reg_email = st.text_input("Email Address", placeholder="elena@eldercare.org")
            reg_password = st.text_input(
                "Password (minimum 8 characters)",
                type="password",
                placeholder="At least 8 characters",
            )
            reg_role = st.selectbox(
                "Account Role",
                options=["caregiver", "admin"],
                format_func=lambda r: "Caregiver (Assigned Residents)" if r == "caregiver" else "Administrator (Full Facility Access)",
            )
            reg_submit = st.form_submit_button("Create Account", type="primary", use_container_width=True)

            if reg_submit:
                if not reg_name.strip() or not reg_email.strip() or len(reg_password) < 8:
                    st.warning("Please provide a valid name, email address, and a password of at least 8 characters.")
                else:
                    try:
                        created_user = auth_service.register(
                            name=reg_name,
                            email=reg_email,
                            password=reg_password,
                            role=reg_role,
                        )
                        st.success(
                            f"Account created for **{created_user.get('name')}** (`{created_user.get('email')}`). "
                            "You can now sign in using the **Sign In** tab."
                        )
                    except APIError as exc:
                        st.error(f"Registration failed: {exc.message}")

