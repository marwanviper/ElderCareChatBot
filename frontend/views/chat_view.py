"""Interactive AI Companion & Care Assistant chat view orchestrated by LangGraph."""

from typing import Any

import streamlit as st

from frontend.components.ui_cards import (
    format_timestamp,
    render_active_resident_banner,
    render_safety_alert_banner,
)
from frontend.services.api_client import APIError
from frontend.services.chat_service import ChatFrontendService


PROVIDER_DISPLAY_NAMES = {
    "gemini": "Google Gemini",
    "openai": "OpenAI GPT-3.5",
}


def render_chat_view(chat_service: ChatFrontendService) -> None:
    """Render the interactive AI Companion Chat powered by LangGraph, Gemini, and OpenAI GPT-3.5."""
    token: str = st.session_state["token"]
    resident: dict[str, Any] | None = st.session_state.get("selected_resident")

    st.title("🤖 AI Companion & Clinical Care Assistant")
    st.caption(
        "Orchestrated with **LangGraph** • Switch seamlessly between **Google Gemini** and **OpenAI GPT-3.5**."
    )
    render_active_resident_banner(resident)

    if not resident:
        return

    resident_id = resident["id"]

    # 1. Fetch available LLM providers & models from backend
    providers_info: list[dict[str, Any]] = []
    try:
        providers_info = chat_service.list_providers(token)
    except APIError as exc:
        st.error(f"Failed to load LLM providers: {exc.message}")
        return

    provider_map = {p["provider"]: p for p in providers_info}
    provider_names = list(provider_map.keys()) or ["gemini", "openai"]

    # 2. Fetch active chat sessions for this resident
    sessions: list[dict[str, Any]] = []
    try:
        sessions = chat_service.list_sessions(
            token=token,
            resident_id=resident_id,
            status_filter="active",
        )
    except APIError as exc:
        st.error(f"Failed to load chat sessions: {exc.message}")
        return

    # 3. Top Control Bar: Session Selector + New Session + LLM Provider & Model Selector
    with st.container(border=True):
        col_sess, col_prov, col_mod, col_temp = st.columns([3, 2, 2, 1.5])

        with col_prov:
            selected_provider = st.selectbox(
                "LLM Provider",
                options=provider_names,
                format_func=lambda p: (
                    f"{PROVIDER_DISPLAY_NAMES.get(p, p.upper())} "
                    f"{'✅' if provider_map.get(p, {}).get('is_configured') else '⚠️ (No Key)'}"
                ),
                key="chat_provider_select",
            )

        p_info = provider_map.get(selected_provider, {})
        avail_models = p_info.get("available_models") or ["gemini-3.5-flash"]
        default_mod = p_info.get("default_model") or avail_models[0]
        mod_index = avail_models.index(default_mod) if default_mod in avail_models else 0

        with col_mod:
            selected_model = st.selectbox(
                "Model",
                options=avail_models,
                index=mod_index,
                key=f"chat_model_select_{selected_provider}",
            )

        with col_temp:
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.4,
                step=0.1,
                key="chat_temperature_slider",
            )

        with col_sess:
            session_options = {
                s["id"]: f"#{s['id']} — {s.get('title') or 'Untitled Session'}"
                for s in sessions
            }
            session_ids = list(session_options.keys())

            active_conv_id = st.session_state.get("active_conversation_id")
            if active_conv_id not in session_ids:
                active_conv_id = session_ids[0] if session_ids else None
                st.session_state["active_conversation_id"] = active_conv_id

            if session_ids:
                chosen_conv_id = st.selectbox(
                    "Active Conversation Session",
                    options=session_ids,
                    index=session_ids.index(active_conv_id) if active_conv_id in session_ids else 0,
                    format_func=lambda cid: session_options.get(cid, f"Session #{cid}"),
                )
                st.session_state["active_conversation_id"] = chosen_conv_id
            else:
                st.info("No active session yet. Start one below.")
                chosen_conv_id = None

        # New session creation bar
        ncol1, ncol2 = st.columns([4, 1.2])
        new_title = ncol1.text_input(
            "New Session Title (optional)",
            placeholder=f"Morning check-in with {resident.get('name')}...",
            label_visibility="collapsed",
        )
        if ncol2.button("➕ New Chat Session", use_container_width=True, type="primary"):
            try:
                created_sess = chat_service.create_session(
                    token=token,
                    resident_id=resident_id,
                    title=new_title or f"Chat with {resident.get('name')}",
                    provider=selected_provider,
                    model=selected_model,
                )
                st.session_state["active_conversation_id"] = created_sess["id"]
                st.rerun()
            except APIError as exc:
                st.error(f"Could not create session: {exc.message}")

        if not p_info.get("is_configured", False):
            st.warning(
                f"**{PROVIDER_DISPLAY_NAMES.get(selected_provider, selected_provider)}** does not have an API key configured in `.env` "
                f"(`GEMINI_API_KEY` or `OPENAI_API_KEY`). Please configure the key or switch to a configured provider before sending messages."
            )

    if not chosen_conv_id:
        return

    # 4. Load and render conversation message history
    try:
        history_resp = chat_service.get_session_history(token, chosen_conv_id)
    except APIError as exc:
        st.error(f"Failed to load conversation history: {exc.message}")
        return

    if isinstance(history_resp, list):
        messages: list[dict[str, Any]] = history_resp
    elif isinstance(history_resp, dict):
        messages = history_resp.get("messages") or []
    else:
        messages = []

    chat_container = st.container(height=460, border=True)
    with chat_container:
        if not messages:
            st.markdown(
                f"👋 *Conversation **#{chosen_conv_id}** is ready. Send a message below to talk with the ElderCare AI Companion for **{resident.get('name')}**.*"
            )
        for msg in messages:
            role = msg.get("role", "user")
            avatar = "🧑‍⚕️" if role == "user" else ("🤖" if role == "assistant" else "⚙️")
            with st.chat_message(role, avatar=avatar):
                st.markdown(msg.get("content", ""))

                extra = msg.get("extra_metadata") or {}
                safety_info = extra.get("safety")
                if safety_info:
                    render_safety_alert_banner(safety_info)

                # Render provider/model/latency/token badges for assistant messages
                pills = [f"🕒 {format_timestamp(msg.get('created_at'))}"]
                if role == "assistant":
                    if extra.get("provider"):
                        pills.append(f"🧠 {extra.get('provider')}/{extra.get('model', '')}")
                    if extra.get("latency_ms") is not None:
                        pills.append(f"⚡ {extra.get('latency_ms')} ms")
                    token_usage = extra.get("token_usage") or {}
                    if token_usage.get("total_tokens"):
                        pills.append(f"🔢 {token_usage.get('total_tokens')} tokens")

                pills_html = "".join(f'<span class="meta-pill">{p}</span>' for p in pills)
                st.markdown(pills_html, unsafe_allow_html=True)

    # 5. Chat Input Box -> LangGraph Execution
    user_prompt = st.chat_input(
        f"Message ElderCare AI ({PROVIDER_DISPLAY_NAMES.get(selected_provider, selected_provider)} • {selected_model})..."
    )
    if user_prompt:
        with st.spinner(
            f"Running LangGraph workflow with {PROVIDER_DISPLAY_NAMES.get(selected_provider, selected_provider)} ({selected_model})..."
        ):
            try:
                turn_response = chat_service.send_message(
                    token=token,
                    conversation_id=chosen_conv_id,
                    content=user_prompt,
                    provider=selected_provider,
                    model=selected_model,
                    temperature=temperature,
                )
                safety = turn_response.get("safety") or {}
                if safety.get("requires_caregiver_alert"):
                    st.toast(
                        "🚨 URGENT: Safety check flagged an emergency indicator in this message!",
                        icon="🚨",
                    )
                st.rerun()
            except APIError as exc:
                st.error(f"AI Generation Error: {exc.message}")

