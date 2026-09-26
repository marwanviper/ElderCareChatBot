# 📚 ElderCare Backend Documentation

Welcome to the comprehensive technical documentation for the **ElderCare ChatBot** backend platform.

---

## 🧭 Documentation Index

| Guide | Description |
| :--- | :--- |
| 🚀 **[README](file:///d:/ElderCareChatBot/docs/README.md)** | System overview, technology stack, directory structure, and quickstart. |
| 🔌 **[API Documentation](file:///d:/ElderCareChatBot/docs/API.md)** | REST endpoints, route definitions, schemas, request/response examples, status codes, and error formatting. |
| 🔑 **[Authentication Guide](file:///d:/ElderCareChatBot/docs/AUTHENTICATION.md)** | Registration, OAuth2 / JSON login flows, JWT token issuance, verification, lifecycle, and security standards. |
| 🛡️ **[Authorization & RBAC](file:///d:/ElderCareChatBot/docs/AUTHORIZATION.md)** | Role-based (`admin` vs `caregiver`) and resource-level access control via `user_resident_permissions`. |
| 📜 **[Logging & Diagnostics](file:///d:/ElderCareChatBot/docs/LOGGING.md)** | Centralized logging configuration, request profiling middleware, error tracing, and PII redaction rules. |
| 🗄️ **[Database Architecture](file:///d:/ElderCareChatBot/docs/DATABASE.md)** | PostgreSQL relational schemas, SQLAlchemy 2.0 models, relationships, indexes, constraints, and migrations. |
| 🛠️ **[Developer Guide](file:///d:/ElderCareChatBot/docs/DEVELOPMENT.md)** | Step-by-step instructions for extending models, creating CRUD routines, adding API routes, and writing tests. |

---

## 🏗️ System Overview

ElderCare ChatBot provides a robust, enterprise-grade backend for managing elderly care operations, caregiver interactions, clinical notes, care plans, adverse incidents, and AI-driven conversational workflows.

### Core Capabilities
* **Full CRUD Operations**: Robust persistence for users, residents, clinical care reports, rehabilitation care goals, incidents, and assignment permissions.
* **Dual-Tier Security**:
  * **Role-Based Access Control (RBAC)**: Strict separation of administrative capabilities from caregiver day-to-day operations.
  * **Resource-Level Scoping**: Caregivers are strictly isolated to residents explicitly assigned to them in `user_resident_permissions`.
* **Standard-Compliant Authentication**: Pure bcrypt password hashing with SHA-256 JWT tokens compatible with OAuth2 and modern single-page applications.
* **Observable Operations**: Non-blocking request timing middleware, structured application logging, and sanitized exception handlers preventing stack leakages.
* **100% Automated Test Coverage**: Comprehensive unit and integration test suite executing against isolated in-memory databases.

---

## 🛠️ Technology Stack

* **Language**: Python 3.11+ / 3.13
* **Web Framework**: FastAPI 0.141+ with Starlette
* **ORM & Database**: SQLAlchemy 2.0, PostgreSQL (production), SQLite / in-memory (testing)
* **Data Validation**: Pydantic v2 & Pydantic-Settings
* **Security & Auth**: PyJWT (HS256 tokens), Bcrypt (password salting & hashing)
* **Application Server**: Uvicorn with ASGI standard
* **Testing Engine**: Python Standard `unittest` + FastAPI `TestClient` (`httpx`)

---

## 📁 Repository Directory Structure

```text
ElderCareChatBot/
├── .env.example                  # Environment configuration template
├── README.md                     # Top-level repository overview
├── requirements.txt              # Project dependencies
├── docs/                         # Architecture and technical documentation
│   ├── README.md                 # Documentation portal
│   ├── API.md                    # REST API endpoint reference
│   ├── AUTHENTICATION.md         # JWT & authentication guide
│   ├── AUTHORIZATION.md          # RBAC & resource permission guide
│   ├── LOGGING.md                # Logging and error handling
│   ├── DATABASE.md               # Schema definitions and ER diagrams
│   └── DEVELOPMENT.md            # Developer workflows and testing guide
├── src/
│   ├── api/                      # Web API Layer
│   │   ├── auth/                 # Authentication routes (/api/v1/auth)
│   │   │   └── routes.py
│   │   ├── routes/               # Resource routers (/api/v1/*)
│   │   │   ├── care_goals.py
│   │   │   ├── care_reports.py
│   │   │   ├── incidents.py
│   │   │   ├── permissions.py
│   │   │   ├── residents.py
│   │   │   └── users.py
│   │   └── deps.py               # Dependency injection (DB, Auth, RBAC)
│   ├── core/                     # Application Core
│   │   ├── config.py             # Pydantic Settings
│   │   ├── logging.py            # Centralized logging configuration
│   │   └── security.py           # Bcrypt & JWT cryptographic utilities
│   ├── crud/                     # Data Access Layer
│   │   ├── care_goal.py
│   │   ├── care_report.py
│   │   ├── incident.py
│   │   ├── resident.py
│   │   ├── user.py
│   │   └── user_resident_permission.py
│   ├── models/                   # SQLAlchemy 2.0 Declarative Models
│   │   ├── care_goal.py
│   │   ├── care_report.py
│   │   ├── incident.py
│   │   ├── resident.py
│   │   ├── user.py
│   │   └── user_resident_permission.py
│   ├── schemas/                  # Pydantic v2 Request/Response Schemas
│   │   ├── auth.py
│   │   ├── care_goal.py
│   │   ├── care_report.py
│   │   ├── incident.py
│   │   ├── resident.py
│   │   ├── user.py
│   │   └── user_resident_permission.py
│   ├── database.py               # Engine and SessionLocal factories
│   └── main.py                   # FastAPI instantiation, middleware, handlers
└── tests/                        # Automated Test Suite
    ├── test_base.py              # In-memory SQLite base setup for CRUD tests
    ├── test_api_base.py          # In-memory TestClient setup for API tests
    ├── test_users.py             # User CRUD unit tests
    ├── test_residents.py         # Resident CRUD unit tests
    ├── test_care_reports.py      # Care Report CRUD unit tests
    ├── test_care_goals.py        # Care Goal CRUD unit tests
    ├── test_incidents.py         # Incident CRUD unit tests
    ├── test_user_resident_permissions.py # Permission CRUD unit tests
    ├── test_api_auth.py          # API Auth integration tests
    ├── test_api_rbac.py          # Role-Based Access Control integration tests
    └── test_api_resources.py     # Resource-level permission integration tests
```

---

## ⚡ Quickstart

### 1. Initialize Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Setup Environment Variables
```powershell
cp .env.example .env
```

### 4. Run Automated Test Suite
```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

### 5. Launch Local Development Server
```powershell
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```
Interactive OpenAPI documentation will be accessible at `http://127.0.0.1:8000/docs`.
