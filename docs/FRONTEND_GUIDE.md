# 🖥️ Streamlit Frontend Guide

This guide explains how to configure, launch, and use the **ElderCare AI Streamlit Frontend** (`frontend/`).

---

## 1. Architecture Overview

The Streamlit frontend is a modular web client (`frontend/app.py`) that communicates exclusively with the FastAPI backend over REST/JSON using `httpx`. It never accesses the database directly and respects all JWT authentication and Role-Based Access Control (RBAC) policies enforced by the backend.

```text
frontend/
├── app.py                     # Main Streamlit entry point & router
├── config.py                  # API base URL & timeout settings
├── services/
│   ├── api_client.py          # httpx wrapper with Bearer token & error handling
│   ├── auth_service.py        # Login, registration, current user, user list
│   ├── care_service.py        # Residents, Care Reports, Care Goals, Incidents, Permissions
│   └── chat_service.py        # LLM Providers, Chat Sessions, LangGraph Message execution
├── components/
│   ├── sidebar.py             # Resident selector, navigation, user badge, sign out
│   └── ui_cards.py            # Custom CSS, active resident banner, clinical safety alerts
└── views/
    ├── login_view.py          # Sign In & Register tabs
    ├── dashboard_view.py      # Facility & active resident KPI overview
    ├── chat_view.py           # Interactive AI Companion Chat (Gemini & OpenAI GPT-3.5)
    ├── conversations_view.py  # Conversation History & Clinical Audit Log
    ├── residents_view.py      # Resident Directory & Admin Permission Management
    ├── care_reports_view.py   # Daily & Clinical Care Reports
    ├── care_goals_view.py     # Rehabilitation & Care Goals
    └── incidents_view.py      # Adverse Incidents & Safety Log
```

---

## 2. Running the Full Stack (Backend + Frontend)

### Step 1: Start the FastAPI Backend (Terminal 1)
```powershell
.\venv\Scripts\uvicorn.exe src.main:app --reload --host 127.0.0.1 --port 8000
```

### Step 2: Start the Streamlit Frontend (Terminal 2)
```powershell
.\venv\Scripts\streamlit.exe run frontend/app.py
```

By default, Streamlit opens at `http://localhost:8501` and connects to `http://127.0.0.1:8000`. To point the frontend at a custom backend URL, set `ELDERCARE_API_URL`:
```powershell
$env:ELDERCARE_API_URL="http://127.0.0.1:8000"
.\venv\Scripts\streamlit.exe run frontend/app.py
```

---

## 3. Core User Workflows

1. **Authentication (`🔐 Sign In` / `📝 Register New Account`):**
   - Register an `admin` account to admit residents and assign caregiver permissions, or sign in as a `caregiver`.
2. **Active Resident Selection (Sidebar):**
   - Select any accessible resident from the sidebar dropdown. All pages (Dashboard, AI Chat, Care Reports, Care Goals, Adverse Incidents, Conversation History) automatically scope to the selected resident.
3. **AI Companion Chat (`🤖 AI Companion Chat`):**
   - Choose between **Google Gemini** (`gemini-2.0-flash`, `gemini-1.5-flash`, `gemini-1.5-pro`) and **OpenAI GPT-3.5** (`gpt-3.5-turbo`, `gpt-3.5-turbo-0125`, `gpt-4o-mini`).
   - Adjust generation temperature (`0.0` – `1.0`).
   - Create or switch active conversation sessions.
   - If a message mentions an acute emergency (e.g., fall, chest pain, breathing distress), a high-visibility **Urgent Caregiver Safety Alert** banner is displayed automatically.

