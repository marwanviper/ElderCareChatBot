"""Main Streamlit entry point for the ElderCareChatBot Frontend Application.

Run with:
    streamlit run frontend/app.py
"""

from pathlib import Path
import sys

# Ensure project root is on sys.path when invoked via `streamlit run frontend/app.py`
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from frontend.components.sidebar import render_sidebar
from frontend.components.ui_cards import apply_custom_css
from frontend.config import frontend_config
from frontend.services.api_client import APIClient
from frontend.services.auth_service import AuthService
from frontend.services.care_service import CareService
from frontend.services.chat_service import ChatFrontendService
from frontend.views.care_goals_view import render_care_goals_view
from frontend.views.care_reports_view import render_care_reports_view
from frontend.views.chat_view import render_chat_view
from frontend.views.conversations_view import render_conversations_view
from frontend.views.dashboard_view import render_dashboard_view
from frontend.views.incidents_view import render_incidents_view
from frontend.views.login_view import render_login_view
from frontend.views.residents_view import render_residents_view


def main() -> None:
    """Initialize Streamlit page configuration, services, and view router."""
    st.set_page_config(
        page_title=frontend_config.APP_TITLE,
        page_icon=frontend_config.APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_custom_css()

    api_client = APIClient()
    auth_service = AuthService(api_client)
    care_service = CareService(api_client)
    chat_service = ChatFrontendService(api_client)

    # Authentication Gate
    token = st.session_state.get("token")
    user = st.session_state.get("user")
    if not token or not user:
        render_login_view(auth_service)
        return

    # Render Sidebar & Route Active Page
    active_page = render_sidebar(care_service)

    if active_page == "📊 Dashboard":
        render_dashboard_view(care_service, chat_service)
    elif active_page == "🤖 AI Companion Chat":
        render_chat_view(chat_service)
    elif active_page == "💬 Conversation History":
        render_conversations_view(chat_service)
    elif active_page == "👥 Residents":
        render_residents_view(care_service, auth_service)
    elif active_page == "📋 Care Reports":
        render_care_reports_view(care_service)
    elif active_page == "🎯 Care Goals":
        render_care_goals_view(care_service)
    elif active_page == "⚠️ Adverse Incidents":
        render_incidents_view(care_service)
    else:
        render_dashboard_view(care_service, chat_service)


if __name__ == "__main__":
    main()

