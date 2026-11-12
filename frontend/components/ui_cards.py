"""Custom styling, badges, and alert banners for the ElderCare Streamlit UI."""

from datetime import datetime
from typing import Any

import streamlit as st


def apply_custom_css() -> None:
    """Inject clean, accessible healthcare-oriented CSS styles."""
    st.markdown(
        """
        <style>
        .eldercare-banner {
            background: linear-gradient(135deg, #0f4c81 0%, #1b6ca8 100%);
            color: #ffffff;
            padding: 1rem 1.35rem;
            border-radius: 10px;
            margin-bottom: 1.2rem;
            box-shadow: 0 2px 6px rgba(15, 76, 129, 0.16);
        }
        .eldercare-banner h3 {
            margin: 0 0 0.25rem 0;
            color: #ffffff;
            font-size: 1.25rem;
        }
        .eldercare-banner p {
            margin: 0;
            opacity: 0.92;
            font-size: 0.92rem;
        }
        .safety-alert-high {
            background-color: #fff1f2;
            border-left: 6px solid #e11d48;
            color: #881337;
            padding: 0.9rem 1.1rem;
            border-radius: 8px;
            margin: 0.6rem 0;
            font-size: 0.95rem;
        }
        .safety-alert-medium {
            background-color: #fffbeb;
            border-left: 6px solid #d97706;
            color: #78350f;
            padding: 0.8rem 1.1rem;
            border-radius: 8px;
            margin: 0.6rem 0;
            font-size: 0.92rem;
        }
        .meta-pill {
            display: inline-block;
            background-color: #f1f5f9;
            color: #334155;
            border: 1px solid #cbd5e1;
            border-radius: 999px;
            padding: 0.15rem 0.65rem;
            font-size: 0.78rem;
            margin-right: 0.4rem;
            margin-top: 0.25rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_timestamp(raw_ts: str | None) -> str:
    """Format an ISO-8601 timestamp string into a human-friendly date/time."""
    if not raw_ts:
        return "N/A"
    try:
        cleaned = raw_ts.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(raw_ts)


def render_active_resident_banner(resident: dict[str, Any] | None) -> None:
    """Render a persistent context bar showing the currently selected resident."""
    if not resident:
        st.info("No resident is currently selected. Select or create a resident from the sidebar or Residents page.")
        return

    name = resident.get("name", "Unknown Resident")
    room = resident.get("room_number") or "Unassigned"
    dob = resident.get("date_of_birth") or "Not specified"
    res_id = resident.get("id", "?")

    st.markdown(
        f"""
        <div class="eldercare-banner">
            <h3>👤 Active Resident: {name} (ID #{res_id})</h3>
            <p>🚪 <strong>Room:</strong> {room} &nbsp;|&nbsp; 🎂 <strong>Date of Birth:</strong> {dob}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_safety_alert_banner(safety_data: dict[str, Any] | None) -> None:
    """Render a visual clinical safety alert if triggered by the LangGraph SafetyChecker."""
    if not safety_data:
        return

    risk_level = safety_data.get("risk_level", "none")
    requires_alert = safety_data.get("requires_caregiver_alert", False)
    categories = (
        safety_data.get("flagged_categories")
        or safety_data.get("triggered_categories")
        or []
    )
    cats_str = ", ".join(categories) if categories else "Clinical concern"

    if risk_level == "high_emergency" or requires_alert:
        st.markdown(
            f"""
            <div class="safety-alert-high">
                <strong>🚨 URGENT CAREGIVER SAFETY ALERT ({risk_level.upper()})</strong><br/>
                Triggered Indicators: <code>{cats_str}</code>.<br/>
                Immediate physical check-in by care staff is recommended. Consider logging an Adverse Incident record.
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif risk_level == "medium":
        st.markdown(
            f"""
            <div class="safety-alert-medium">
                <strong>⚠️ Clinical Attention Flag ({risk_level.upper()})</strong><br/>
                Detected Topics: <code>{cats_str}</code>. Follow up during the next care round.
            </div>
            """,
            unsafe_allow_html=True,
        )

